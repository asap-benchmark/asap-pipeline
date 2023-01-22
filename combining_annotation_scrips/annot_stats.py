import os
import json
import glob
import csv
import re
import random
import itertools
import numpy as np
import pdb
import random
random.seed(0)

# generate weighted combinations of chains
# for generating the chains above 3 length
def generate_combinations(chain_len, num_samples=50):
    atomic_events = ['0','1','2','3','4','5','6','7','8','9','o','w']
    weights = [80, 40, 10, 10, 20, 10, 20, 1, 0, 0, 20, 10]
    n = 0
    combinations = {}
    options = []

    while n < num_samples:
        # print(n)
        chain = random.choices(atomic_events, weights=weights, k=chain_len)
        key = ' '.join(chain)
        if key not in combinations:
            combinations[key] = 1
            options.append(chain)
            n += 1

    return options

def generate_score_bounds(chain_len, num_overs):
    if num_overs >=1 and num_overs <=2:
        temp = []
        for i in range(chain_len):
            temp.append(list(np.arange(1,2)))    ### (1,3)
        a = list(itertools.product(*temp))
        if len(a)>50:
            a = random.sample(a, 50)
        return a
    elif num_overs >=3 and num_overs <=4:
        temp = []
        for i in range(chain_len):
            temp.append(list(np.arange(1,3)))   ### (2,4)
        a = list(itertools.product(*temp))
        if len(a)>50:
            a = random.sample(a, 50)
        return a
    elif num_overs >=5 and num_overs <=6:
        temp = []
        for i in range(chain_len):
            temp.append(list(np.arange(1,4)))   ### (3,6)
        a = list(itertools.product(*temp))
        if len(a)>50:
            a = random.sample(a, 50)
        return a
    elif num_overs >=7 and num_overs <=8:
        temp = []
        for i in range(chain_len):
            temp.append(list(np.arange(2,5)))    ### (3.7)
        a = list(itertools.product(*temp))
        if len(a)>50:
            a = random.sample(a, 50)
        return a
    elif num_overs >=9 and num_overs <=10:
        temp = []
        for i in range(chain_len):
            temp.append(list(np.arange(2,6)))     ### (4,8)
        a = list(itertools.product(*temp))
        if len(a)>50:
            a = random.sample(a, 50)
        return a
        

def generate_score_bounds_inrange(chain_len, num_overs):
    if num_overs >=1 and num_overs <=2:
        events = [[0,3], [0,1], [0,2], [1,3], [2,3], [1,2]]
        a = list(itertools.combinations(events, chain_len))
        if len(a)>50:
            a = random.sample(a, 50)
        return a
    elif num_overs >=3 and num_overs <=4:
        events = [[0,4], [0,3], [0,1], [0,2], [1,4], [1,3], [2,4], [2,3], [3,4], [1,2]]
        a = list(itertools.combinations(events, chain_len))
        if len(a)>50:
            a = random.sample(a, 50)
        return a
    elif num_overs >=5 and num_overs <=6:
        events = [[0,5], [0,4], [0,3], [0,1], [0,2], [1,5], [1,4], [1,3], [2,5], [2,4], [2,3], [3,5], [3,4], [4,5], [1,2]]
        a = list(itertools.combinations(events, chain_len))
        if len(a)>50:
            a = random.sample(a, 50)
        return a
    elif num_overs >=7 and num_overs <=8:
        events = [[1,6], [1,5], [1,4], [1,3], [1,2], [2,6], [2,5], [2,4], [2,3], [3,6], [3,5], [3,4], [4,6], [4,5], [5,6]]
        a = list(itertools.combinations(events, chain_len))
        if len(a)>50:
            a = random.sample(a, 50)
        return a
    elif num_overs >=9 and num_overs <=10:
        events = [[1,7], [1,6], [1,5], [1,4], [1,3], [1,2], [2,7], [2,6], [2,5], [2,4], [2,3], [3,7], [3,6], [3,5], [3,4], [4,7], [4,6], [4,5], [5,7], [5,6], [6,7]]
        a = list(itertools.combinations(events, chain_len))
        if len(a)>50:
            a = random.sample(a, 50)
        return a
        

# generate combinations of length 1-3
def get_combinations(chain_len):
    atomic_events = ['0','1','2','3','4','5','6','7','8','9','o','w']
    options = []
    for e1 in atomic_events:
        if (chain_len > 1):
            for e2 in atomic_events:
                if chain_len > 2:
                    for e3 in atomic_events:
                            options.append((e1,e2,e3))
                else:
                    options.append((e1,e2))
        else:
            options.append((e1))
    return options

def get_combinations_AND_OR(chain_len):
    ## Just need all combinations with no order necessary and also no repetitions
    atomic_events = ['0','1','2','3','4','5','6','7','8','9','o','w']
    a = list(itertools.combinations(atomic_events, chain_len))
    if len(a) > 400:
        a = random.sample(a, 400)
    return a


# function for getting chained event stats
def get_ann_chain_stats(match_annotations, chain_len, combinations=None):
    stats = [{} for i in range(len(match_annotations) + 1)]
    k = 0
    if combinations is not None and chain_len > 3:
        options = generate_combinations(chain_len)
    elif combinations is not None:
        options = get_combinations(chain_len)
    else:
        options = combinations

    for j, annotations in enumerate(match_annotations):
        stats[j+1]['name'] = annotations[0]['name'] # new annotations
        i = 0
        while i < len(annotations):
            chain = annotations[i]['chains']
            for option in options:
                regex_str = ''
                for a in option:
                    regex_str += a + '.*'
                regex_str = regex_str[:-2]
                res = re.search(regex_str, chain)
                if res is not None:
                    key = ' '.join(option)
                    if key not in stats[0]:
                        stats[0][key] = 1
                        stats[j+1][key] = 1
                    else: 
                        stats[0][key] += 1
                        if key not in stats[j+1]:
                            stats[j+1][key] = 1
                        else:
                            stats[j+1][key] += 1
            i += 1
            k += 1
        for key, value in stats[j+1].items():
            if type(value) == int:
                stats[j+1][key] /= i
    '''
    for annotations in match_annotations:
        i = 0
        while i < len(annotations):
            for chain in annotations[i]['chains_2']:
                if chain not in stats:
                    stats[chain] = 1
                else: stats[chain] += 1
            for chain in annotations[i]['chains_3']:
                if chain not in stats:
                    stats[chain] = 1
                else: stats[chain] += 1
            for chain in annotations[i]['chains_4']:
                if chain not in stats:
                    stats[chain] = 1
                else: stats[chain] += 1
            i += 1
            k += 1
        '''

    # get percentages
    for key, value in stats[0].items():
        if type(value) == int:
            stats[0][key] /= k
    
    return stats


# function for getting AND/OR BASED EVENTS WITH ATLEAST/ATMOST/INRANGE
def get_ann_chain_stats_and_or(match_annotations, chain_len, num_overs, op= 'atleast', combo='AND'):
    ## op can be 'atleast', 'atmost', 'inrange'
    ## combo can be 'AND', 'OR'
    ## at max chain_len for this can be 12 (number of atomic events)
    stats = [{} for i in range(len(match_annotations) + 1)]
    # print(stats)
    k = 0
    options = get_combinations_AND_OR(chain_len)
    bounds = generate_score_bounds(chain_len, num_overs)
    print('Total number of combinations: ', len(options))
    print('Total number of bounds: ', len(bounds))
    # print(bounds)
    # print(options)

    for j, annotations in enumerate(match_annotations):
        try:
            stats[j+1]['name'] = annotations[0]['name'] # new annotations
        except:
            pdb.set_trace()
        i = 0
        print('Annotation name: ', annotations[0]['name'])
        while i < len(annotations):
            chain = annotations[i]['chains']
            for option in options:
                for bound in bounds:
                    # print(bound)
                    res = []
                    for idx in range(len(option)):
                        regex_str = option[idx]
                        num_occ = re.findall(regex_str, chain)

                        if op=='atleast':
                            if len(num_occ) >= bound[idx]:
                                res.append(True)
                            else:
                                res.append(False)
                        elif op=='atmost':
                            if len(num_occ) <= bound[idx]:
                                res.append(True)
                            else:
                                res.append(False)
                        
                    if combo == 'AND':
                        val = all(res)
                    elif combo == 'OR':
                        val = any(res)
                    if val:
                        key = ''
                        for idx in range(len(bound)-1):
                            key += op + ' ' + str(bound[idx]) + ' ' + str(option[idx]) + '\'s ' + combo + ' '
                        key += op + ' ' + str(bound[len(bound)-1]) + ' ' + str(option[len(bound)-1]) + '\'s'
                        if key not in stats[0]:
                            stats[0][key] = 1
                            stats[j+1][key] = 1
                        else:
                            stats[0][key] += 1
                            if key not in stats[j+1]:
                                stats[j+1][key] = 1
                            else:
                                stats[j+1][key] += 1
                    # if res is not None:
                    #     key = ' '.join(option)
                    #     if key not in stats[0]:
                    #         stats[0][key] = 1
                    #         stats[j+1][key] = 1
                    #     else: 
                    #         stats[0][key] += 1
                    #         if key not in stats[j+1]:
                    #             stats[j+1][key] = 1
                    #         else:
                    #             stats[j+1][key] += 1
            i += 1
            k += 1

            # print('Done')
        # pdb.set_trace()
        for key, value in stats[j+1].items():
            if type(value) == int:
                stats[j+1][key] /= i
        # print(i)
        print('Done')

    # get percentages
    for key, value in stats[0].items():
        if type(value) == int:
            stats[0][key] /= k
    
    return stats


def get_ann_chain_stats_and_or_multi(match_annotations, chain_len, num_overs, op= ['atleast', 'atmost'], combo='AND'):
    ## op can be 'atleast', 'atmost', 'inrange'
    ## combo can be 'AND', 'OR'
    ## at max chain_len for this can be 12 (number of atomic events)
    stats = [{} for i in range(len(match_annotations) + 1)]
    # print(stats)
    k = 0
    options = get_combinations_AND_OR(chain_len)
    bounds = generate_score_bounds(chain_len, num_overs)
    print('Total number of combinations: ', len(options))
    print('Total number of bounds: ', len(bounds))
    # print(bounds)
    # print(options)

    for j, annotations in enumerate(match_annotations):
        stats[j+1]['name'] = annotations[0]['name'] # new annotations
        i = 0
        print('Annotation name: ', annotations[0]['name'])
        while i < len(annotations):
            chain = annotations[i]['chains']
            for option in options:
                for bound in bounds:
                    # print(bound)
                    res = []
                    for idx in range(len(option)):
                        regex_str = option[idx]
                        num_occ = re.findall(regex_str, chain)

                        if op[idx]=='atleast':
                            if len(num_occ) >= bound[idx]:
                                res.append(True)
                            else:
                                res.append(False)
                        elif op[idx]=='atmost':
                            if len(num_occ) <= bound[idx]:
                                res.append(True)
                            else:
                                res.append(False)
                        
                    if combo == 'AND':
                        val = all(res)
                    elif combo == 'OR':
                        val = any(res)
                    if val:
                        key = ''
                        for idx in range(len(bound)-1):
                            key += op[idx] + ' ' + str(bound[idx]) + ' ' + str(option[idx]) + '\'s ' + combo + ' '
                        key += op[len(bound)-1] + ' ' + str(bound[len(bound)-1]) + ' ' + str(option[len(bound)-1]) + '\'s'
                        if key not in stats[0]:
                            stats[0][key] = 1
                            stats[j+1][key] = 1
                        else:
                            stats[0][key] += 1
                            if key not in stats[j+1]:
                                stats[j+1][key] = 1
                            else:
                                stats[j+1][key] += 1
                    # if res is not None:
                    #     key = ' '.join(option)
                    #     if key not in stats[0]:
                    #         stats[0][key] = 1
                    #         stats[j+1][key] = 1
                    #     else: 
                    #         stats[0][key] += 1
                    #         if key not in stats[j+1]:
                    #             stats[j+1][key] = 1
                    #         else:
                    #             stats[j+1][key] += 1
            i += 1
            k += 1

            # print('Done')
        # pdb.set_trace()
        for key, value in stats[j+1].items():
            if type(value) == int:
                stats[j+1][key] /= i
        # print(i)

    # get percentages
    for key, value in stats[0].items():
        if type(value) == int:
            stats[0][key] /= k
    
    return stats


def get_ann_chain_stats_inrange(match_annotations, chain_len, num_overs, op= 'inrange', combo='AND'):
    ## op can be 'atleast', 'atmost', 'inrange'
    ## combo can be 'AND', 'OR'
    ## at max chain_len for this can be 12 (number of atomic events)
    stats = [{} for i in range(len(match_annotations) + 1)]
    # print(stats)
    k = 0
    options = get_combinations_AND_OR(chain_len)
    bounds = generate_score_bounds_inrange(chain_len, num_overs)
    print('Total number of combinations: ', len(options))
    print('Total number of bounds: ', len(bounds))
    # print(bounds)
    # print(options)

    for j, annotations in enumerate(match_annotations):
        stats[j+1]['name'] = annotations[0]['name'] # new annotations
        i = 0
        print('Annotation name: ', annotations[0]['name'])
        while i < len(annotations):
            chain = annotations[i]['chains']
            for option in options:
                for bound in bounds:
                    # print(bound)
                    res = []
                    for idx in range(len(option)):
                        regex_str = option[idx]
                        num_occ = re.findall(regex_str, chain)

                        if op=='inrange':
                            if len(num_occ) >= bound[idx][0] and len(num_occ) <= bound[idx][1]:
                                res.append(True)
                            else:
                                res.append(False)
                        
                    if combo == 'AND':
                        val = all(res)
                    elif combo == 'OR':
                        val = any(res)
                    if val:
                        key = ''
                        for idx in range(len(bound)-1):
                            key += str(option[idx]) + ' ' + op + ' ' + str(bound[idx]) + ' ' + combo + ' '
                        key += str(option[len(bound)-1]) + ' ' + op + ' ' + str(bound[len(bound)-1])
                        if key not in stats[0]:
                            stats[0][key] = 1
                            stats[j+1][key] = 1
                        else:
                            stats[0][key] += 1
                            if key not in stats[j+1]:
                                stats[j+1][key] = 1
                            else:
                                stats[j+1][key] += 1
                    # if res is not None:
                    #     key = ' '.join(option)
                    #     if key not in stats[0]:
                    #         stats[0][key] = 1
                    #         stats[j+1][key] = 1
                    #     else: 
                    #         stats[0][key] += 1
                    #         if key not in stats[j+1]:
                    #             stats[j+1][key] = 1
                    #         else:
                    #             stats[j+1][key] += 1
            i += 1
            k += 1

            # print('Done')
        # pdb.set_trace()
        for key, value in stats[j+1].items():
            if type(value) == int:
                stats[j+1][key] /= i
        # print(i)

    # get percentages
    for key, value in stats[0].items():
        if type(value) == int:
            stats[0][key] /= k
    
    return stats

# function for getting combined annotations statistics
def get_ann_combine_stats (annotations, suffix='_combined', fps=30):
    def appeared_more (player_list, p1, scored) -> bool:
        if len(player_list) != len(scored):
            raise ValueError('Batter list annotation and scored list not same length.') 
        m = 0 
        for i in range(len(player_list)):
            if scored[i] == 1:
                m += 1 if (p1 == player_list[i]) else -1
        return m > 0

    stats = {'name': '', 
            'total_sequences': 0, 
            'max_balls_len': 0, 
            'min_balls_len': 0,
            'avg_balls_len': 0, 
            'avg_num_boundaries': 0,
            'scored': 0, 
            'out': 0, 
            'wide': 0,
            'p1_scored_more': 0,
            'p1_hit_more': 0,
            'runs': 0,
            '0<runs<=b/3': 0,
            'b/3<runs<=2b/3': 0,
            '2b/3<runs<=b': 0,
            'b<runs': 0}
    i = 0
    min_len, max_len, avg_len = 1e9, 0.0, 0.0
    num_scored, num_wide, num_out = 0, 0, 0

    while i < len(annotations):
        num_balls = annotations[i]['balls']
        duration = (annotations[i]['end'] - annotations[i]['start'])/fps
        num_scored += 1 if annotations[i]['stats'][0] == 'SCORED' else 0
        num_out += 1 if annotations[i]['stats'][1] == 'OUT' else 0
        num_wide += 1 if annotations[i]['stats'][2] == 'WIDE' else 0

        # run stats
        stats['avg_num_boundaries'] += annotations[i]['num_boundaries']
        stats['runs'] += annotations[i]['runs']
        stats['0<runs<=b/3'] += (0 < annotations[i]['runs'] <= num_balls/3)
        stats['b/3<runs<=2b/3'] += (num_balls/3 < annotations[i]['runs'] <= 2*num_balls/3)
        stats['2b/3<runs<=b'] += (2*num_balls/3 < annotations[i]['runs'] <= num_balls)
        stats['b<runs'] += (num_balls < annotations[i]['runs'])

        # bowler/batter stats
        stats['p1_scored_more'] += appeared_more(annotations[i]['batters'], annotations[i]['batters'][0], [i == 'SCORED' for i in annotations[i]['scored']])
        stats['p1_hit_more'] += appeared_more(annotations[i]['batters'], annotations[i]['batters'][0], [1] * num_balls)

        if min_len > duration:
            min_len = duration
        if max_len < duration:
            max_len = duration
        avg_len += duration
        i += 1

    stats['name'] = annotations[0]['name'] + suffix
    stats['min_balls_len'] = min_len
    stats['max_balls_len'] = max_len
    stats['scored'] = num_scored / i
    stats['out'] = num_out / i
    stats['wide'] = num_wide / i
    stats['avg_num_boundaries'] /= i
    stats['total_sequences'] = i
    stats['0<runs<=b/3'] /= i
    stats['b/3<runs<=2b/3'] /= i
    stats['2b/3<runs<=b'] /= i
    stats['b<runs'] /= i
    stats['p1_scored_more'] /= i
    stats['p1_hit_more'] /= i
    stats['avg_balls_len'] = avg_len / i
    stats['runs'] /= i
    return stats

# function for getting annotations statistics
def get_ann_stats (annotations, fps=30):
    stats = {'name': '', 
            'total_balls': 0, 
            'max_ball': 0, 
            'min_ball': 0,
            'max_ball_len': 0, 
            'min_ball_len': 0,
            'avg_ball_len': 0, 
            'scored': 0, 
            'out': 0, 
            'wide': 0,
            'runs': {}}
    i, j = 0, 0
    min_len, max_len, avg_len = fps*900,0.0,0.0
    min_over, max_over = 0.0, 0.0
    num_scored, num_wide, num_out = 0, 0, 0

    while i < len(annotations):
        duration = (annotations[i][3] - annotations[i][2])/fps
        num_scored += 1 if annotations[i][7][0] == 'SCORED' else 0
        num_out += 1 if annotations[i][7][1] == 'OUT' else 0
        num_wide += 1 if annotations[i][7][2] == 'WIDE' else 0
        if annotations[i][6] not in stats['runs']:
            stats['runs'][annotations[i][6]] = 1
        else: stats['runs'][annotations[i][6]] += 1
        # ignore > 15 min overs
        if duration > 900:
            pass
        else:
            if min_len > duration:
                min_len = duration
                min_over = annotations[i][1]
            if max_len < duration:
                max_len = duration
                max_over = annotations[i][1]
            avg_len += duration
            j += 1
        i += 1

    avg_len /= j
    stats['name'] = annotations[0][0]
    stats['min_ball_len'] = min_len
    stats['max_ball_len'] = max_len
    stats['min_ball'] = min_over
    stats['max_ball'] = max_over
    stats['scored'] = num_scored / i
    stats['out'] = num_out / i
    stats['wide'] = num_wide / i
    stats['total_balls'] = i
    stats['avg_ball_len'] = avg_len
    
    return stats