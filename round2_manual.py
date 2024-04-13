prices = {
    'pizza': { 'pizza': 1, 'wasabi': 0.48, 'snowball': 1.52, 'shells': 0.71 },
    'wasabi': { 'pizza': 2.05, 'wasabi': 1, 'snowball': 3.26, 'shells': 1.56 },
    'snowball': { 'pizza': 0.64, 'wasabi': 0.3, 'snowball': 1, 'shells': 0.46 },
    'shells': { 'pizza': 1.41, 'wasabi': 0.61, 'snowball': 2.08, 'shells': 1 }
}

import itertools

max_score = 1
for path in itertools.product(['pizza', 'wasabi', 'snowball', 'shells'], repeat=4):
    score = 1
    score *= prices['shells'][path[0]]
    score *= prices[path[0]][path[1]]
    score *= prices[path[1]][path[2]]
    score *= prices[path[2]][path[3]]
    score *= prices[path[3]]['shells']

    if score >= max_score:
        print(path, score)
        max_score = score