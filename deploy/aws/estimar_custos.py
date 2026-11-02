#!/usr/bin/env python3
"""Estimativa mensal do Nautam na AWS, com preços oficiais da AWS Price List API.

Compara sa-east-1 (São Paulo) e us-east-1 (Virgínia), 730 h/mês, preços sob demanda.
Rodar no AWS CloudShell (já tem AWS CLI e Python):

    python3 deploy/aws/estimar_custos.py
    python3 deploy/aws/estimar_custos.py --com-dashboard

Só faz chamadas de leitura à Price List API (gratuita). Não cria recursos.
Itens de uso variável (Amplify, transferência de dados) ficam fora do total
e são listados como observação.
"""
import argparse
import json
import subprocess
import sys

HORAS_MES = 730
REGIOES = ["sa-east-1", "us-east-1"]

# Premissas de dimensionamento (ajuste aqui e rode de novo)
API_VCPU, API_GB = 0.25, 0.5          # tarefa Fargate da API
DASH_VCPU, DASH_GB = 0.5, 1.0         # tarefa Fargate do dashboard (opcional)
ALB_LCU_MEDIO = 0.5                   # tráfego baixo de POC
RDS_STORAGE_GB = 20                   # gp3, mínimo prático
SECRETS = 2                           # DATABASE_URL + reserva
LOGS_GB_MES = 1.0                     # ingestão CloudWatch Logs (retenção curta)
ECR_GB = 2.0                          # imagens versionadas (com política de limpeza)


def get_products(service, filtros):
    args = ["aws", "pricing", "get-products", "--region", "us-east-1",
            "--service-code", service, "--output", "json", "--filters"]
    args += [f"Type=TERM_MATCH,Field={k},Value={v}" for k, v in filtros.items()]
    itens, token = [], None
    while True:
        cmd = args + (["--next-token", token] if token else [])
        out = json.loads(subprocess.check_output(cmd))
        itens += [json.loads(p) for p in out.get("PriceList", [])]
        token = out.get("NextToken")
        if not token:
            return itens


def preco_usd(produto):
    """Primeiro preço sob demanda > 0 (primeira faixa, quando houver faixas)."""
    for termo in produto["terms"].get("OnDemand", {}).values():
        dims = sorted(termo["priceDimensions"].values(),
                      key=lambda d: float(d.get("beginRange", "0") or 0))
        for d in dims:
            v = float(d["pricePerUnit"].get("USD", "0"))
            if v > 0:
                return v
    return None


def achar(service, filtros, cond=lambda attrs: True, nome=""):
    for p in get_products(service, filtros):
        attrs = p["product"].get("attributes", {})
        if cond(attrs):
            v = preco_usd(p)
            if v is not None:
                return v
    raise SystemExit(f"Preço não encontrado: {nome} {filtros}")


def precos(regiao):
    rc = {"regionCode": regiao}
    ut = lambda frag, excl=(): (lambda a: frag in a.get("usagetype", "")
                                and not any(x in a.get("usagetype", "") for x in excl))
    return {
        "fargate_vcpu_h": achar("AmazonECS", rc,
                                ut("Fargate-vCPU-Hours:perCPU", ("ARM", "Windows", "Spot")), "Fargate vCPU"),
        "fargate_gb_h": achar("AmazonECS", rc,
                              ut("Fargate-GB-Hours", ("ARM", "Windows", "Spot", "Ephemeral")), "Fargate GB"),
        "alb_h": achar("AWSELB", {**rc, "productFamily": "Load Balancer-Application"},
                       ut("LoadBalancerUsage"), "ALB hora"),
        "alb_lcu_h": achar("AWSELB", {**rc, "productFamily": "Load Balancer-Application"},
                           ut("LCUUsage"), "ALB LCU"),
        "rds_h": achar("AmazonRDS", {**rc, "productFamily": "Database Instance",
                                     "instanceType": "db.t4g.micro",
                                     "databaseEngine": "PostgreSQL",
                                     "deploymentOption": "Single-AZ"},
                       nome="RDS db.t4g.micro"),
        "rds_gp3_gb": achar("AmazonRDS", {**rc, "productFamily": "Database Storage",
                                          "volumeType": "General Purpose-GP3",
                                          "databaseEngine": "PostgreSQL",
                                          "deploymentOption": "Single-AZ"},
                            nome="RDS gp3"),
        "ipv4_h": achar("AmazonVPC", rc, ut("PublicIPv4:InUseAddress"), "IPv4 público"),
        "secret_mes": achar("AWSSecretsManager", rc, ut("AWSSecretsManager-Secrets"), "Secret"),
        "logs_gb": achar("AmazonCloudWatch", rc, ut("DataProcessing-Bytes", ("VendedLog",)), "Logs"),
        "ecr_gb": achar("AmazonECR", rc, ut("TimedStorage-ByteHrs"), "ECR"),
    }


def custos(p, com_dashboard):
    vcpu = API_VCPU + (DASH_VCPU if com_dashboard else 0)
    gb = API_GB + (DASH_GB if com_dashboard else 0)
    tarefas = 1 + (1 if com_dashboard else 0)
    ips = tarefas + 2  # IP público por tarefa (sub-rede pública) + ALB em 2 AZs
    return {
        "Fargate (tarefas)": (vcpu * p["fargate_vcpu_h"] + gb * p["fargate_gb_h"]) * HORAS_MES,
        "Application Load Balancer": (p["alb_h"] + ALB_LCU_MEDIO * p["alb_lcu_h"]) * HORAS_MES,
        "IPv4 públicos": ips * p["ipv4_h"] * HORAS_MES,
        "RDS db.t4g.micro": p["rds_h"] * HORAS_MES,
        "RDS armazenamento gp3": RDS_STORAGE_GB * p["rds_gp3_gb"],
        "Secrets Manager": SECRETS * p["secret_mes"],
        "CloudWatch Logs": LOGS_GB_MES * p["logs_gb"],
        "ECR": ECR_GB * p["ecr_gb"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--com-dashboard", action="store_true",
                    help="inclui a 2ª tarefa Fargate do Streamlit")
    a = ap.parse_args()
    tabela = {r: custos(precos(r), a.com_dashboard) for r in REGIOES}
    itens = list(next(iter(tabela.values())).keys())
    print(f"\nEstimativa mensal (USD, sob demanda, {HORAS_MES} h)"
          f" — dashboard no ECS: {'sim' if a.com_dashboard else 'não'}\n")
    print(f"{'Item':<28}" + "".join(f"{r:>14}" for r in REGIOES))
    for i in itens:
        print(f"{i:<28}" + "".join(f"{tabela[r][i]:>14.2f}" for r in REGIOES))
    print(f"{'TOTAL':<28}" + "".join(f"{sum(tabela[r].values()):>14.2f}" for r in REGIOES))
    print("\nFora do total (uso variável): Amplify Hosting (minutos de build, GB servidos),"
          "\ntransferência de dados para a internet, snapshots além do tamanho do banco."
          "\nSem NAT Gateway: as tarefas usam sub-rede pública com IP público e entrada"
          "\nrestrita ao security group do ALB.\n")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.exit(f"Falha ao chamar a AWS CLI: {e}")
