module.exports = {
  ci: {
    collect: {
      url: [process.env.LIGHTHOUSE_URL || 'http://localhost:3000'],
      numberOfRuns: 3,
    },
    assert: {
      assertions: {
        'categories:performance': ['warn', { minScore: 0.8 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['warn', { minScore: 0.8 }],
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
}
