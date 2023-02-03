# coding: utf-8

import io
import os
import json
import glob
import csv
import pdb
from annot_stats import (
    get_ann_combine_stats, 
    get_ann_stats, 
    get_ann_chain_stats,
    generate_combinations,
    get_ann_chain_stats_and_or,
    get_ann_chain_stats_inrange,
    get_ann_chain_stats_and_or_multi
)
import re

total_incorrect_order = 0
total_time_over = 0

def stringify (lst):
    if len(lst) < 1:
        return []

    event_chains,event_chains_final = [],[]
    for event in lst[0]:
        event_chains.append([event])

    for events in lst[1:]:
        event_chains_final = []
        for event in events:
            for chain in event_chains:
                event_chains_final.append(chain + [event])
        event_chains = event_chains_final

    
    for chains in event_chains_final:
        key = ""
        for event in chains:
            key += event + " "
        event_chains.append(key)
            
    return event_chains

# function for cleaning annotation errors
def clean_ann_before (annotations):
    global total_incorrect_order
    # wrong ordered overs
    i = 0
    prev = 0
    wrong_overs = 0
    wrong_overs_list = []
    new_annotations = []

    while i < len(annotations):
        if prev > annotations[i][1] and annotations[i][1] != 0.1:
            wrong_overs += 1
            wrong_overs_list.append(annotations[i][1])
        elif (annotations[i][3] - annotations[i][2]) > 20000:
            wrong_overs += 1
            wrong_overs_list.append(annotations[i][1])
        else:
            ann = {'name': '', 
               'overs': 0, 
               'start': 0, 
               'end': 0, 
               'batter': '',
               'bowler': '', 
               'runs': 0, 
               'balls': 0, 
               'stats': ['','','']}

            # set name
            ann['name'] = annotations[i][0] 
            # append overs
            ann['overs'] = annotations[i][1]
            # OR scored, not-out, not-wide
            ann['stats'][0] = 'SCORED' if annotations[i][7][0] == 'SCORED' else 'NOT-SCORED'
            ann['stats'][1] = 'OUT' if annotations[i][7][1] == 'OUT' else 'NOT-OUT'
            ann['stats'][2] = 'WIDE' if annotations[i][7][2] == 'WIDE' else 'NOT-WIDE'
        
            # start/end timestamp
            ann['start'] = annotations[i][2]
            ann['end'] = annotations[i][3]
            # batter and bowlers
            ann['batter'] = annotations[i][4]
            ann['bowler'] = annotations[i][5] 
            # number of total runs
            ann['runs'] = annotations[i][6]
            # number of total balls
            ann['balls'] = 1
            
            # append annotations
            new_annotations.append(ann)
        prev = annotations[i][1]
        i += 1

    print('statistics for json file: ', annotations[0][0])
    # subtract 1 for batting team switch
    print('Incorrectly ordered overs: ', wrong_overs)
    print('List of incorrect orders:')
    for over in wrong_overs_list:
        print(over)
    total_incorrect_order += wrong_overs-1

    return new_annotations

def clean_ann_after (annotations, fps=30):
    global total_time_over
    i = 0
    over_time = 0
    over_time_list = []
    new_annotations = []
    while i < len(annotations):
        if (annotations[i]['end'] - annotations[i]['start'])/fps > 10000:
            over_time += 1
            over_time_list.append(annotations[i]['overs'])
        else:
            new_annotations.append(annotations[i])
        i += 1

    # print('statistics for json file: ', annotations[0][0])
    # subtract 1 for batting team switch
    print('# of times > 10 min: ', over_time)
    print('List of overtime overs:')
    for overs in over_time_list:
        print(overs)
    total_time_over += over_time

    return new_annotations

# function for combining run annotations
def combine_ann_overs (annotations, combine_len: int, all_queries=None):

    def appeared_more (player_list, p1, scored) -> bool:
        if len(player_list) != len(scored):
            raise ValueError('Batter list annotation and scored list not same length.') 
        m = 0 
        for i in range(len(player_list)):
            if scored[i] == 1:
                m += 1 if (p1 == player_list[i]) else -1
        return m > 0

    if len(annotations) < combine_len:
        raise ValueError('Not enough annotations for combine size')

    combined_annots = []


    i = 0
    # quite inefficient, but for purposes of density param, this will do.
    while i < len(annotations): 
        ann = {'name': '', 
               'overs': [], 
               'start': 0, 
               'end': 0, 
               'batters': [],
               'bowlers': [], 
               'wide': [], 
               'out': [],
               'num_wide': 0, 
               'num_out': 0,
               'runs': 0, 
               'balls': 0,
               'num_boundaries': 0,
               'chains': [],
               'stats': ['','',''], 
               'scored': []}

        # if all_queries != None:
        #     ann['logical_queries'] = query_dict
        if all_queries!=None:
            all_query_keys = list(all_queries.keys())
            query_dict = dict.fromkeys(all_query_keys)


        curr_over = prev_over = int(annotations[i]['overs'])
        runs, num_balls, j = 0, 0, 0
        scored, out, wide = False, False, False

        # chain events; order of importance goes out,wide,4/6 ball,scored,none
        to_append, chain = "", ""

        # start timestamp
        ann['start'] = annotations[i]['start']
        
        # combine certain number of overs
        while j < combine_len:
            to_append = "" # set string to nothing happened
            annot = annotations[i]

            # poorly structured, fix after
            if curr_over != prev_over:
                prev_over = curr_over
                j += 1
            if j >= combine_len:
                i -= 1
                break;

            # set name
            ann['name'] = annot['name'] 
            ann['overs'].append(annotations[i]['overs'])
            # append bowler, batter
            ann['batters'].append(annotations[i]['batter'])
            ann['bowlers'].append(annotations[i]['bowler'])
            # sum balls and runs
            runs += annotations[i]['runs']

            # add scored balls
            to_append += (str(annotations[i]['runs']))
            # OR scored, not-out, not-wide
            ann['scored'].append(annotations[i]['stats'][0])
            ann['out'].append(annotations[i]['stats'][1])
            ann['wide'].append(annotations[i]['stats'][2])
            
            # total number of wide, out in game
            if annotations[i]['stats'][0] == 'SCORED':
                if not scored:
                    scored = True
            if annotations[i]['stats'][2] == 'WIDE': 
                to_append += "w"
                ann['num_wide'] += 1 
            if annotations[i]['stats'][1] == 'OUT': 
                to_append += "o"
                ann['num_out'] += 1 
            
            # number of boundaries
            ann['num_boundaries'] += (annotations[i]['runs'] - (1 if annotations[i]['stats'][2] == 'WIDE' else 0) == 4 or
            annotations[i]['runs'] - (1 if annotations[i]['stats'][2] == 'WIDE' else 0) >= 6)
            
            num_balls += 1
            chain += to_append + " "
            ann['chains'] = chain
            # chain_3.append(to_append)
            # chain_4.append(to_append)

            # if num_balls > 2:
            #     chain_2.pop(0)
            #    for chain in stringify(chain_2):
            #        ann['chains_2'][chain] = True
            # if num_balls > 3:
            #    chain_3.pop(0)
            #    for chain in stringify(chain_3):
            #        ann['chains_3'][chain] = True
            #if num_balls > 4:
            #    chain_4.pop(0)
            #    for chain in stringify(chain_4):
            #        ann['chains_4'][chain] = True

            if i+1 < len(annotations) and j < combine_len:
                i += 1
                curr_over = int(annotations[i]['overs'])
            else:
                break
        

        # end timestamp
        ann['end'] = annotations[i]['end']
        # number of total runs
        ann['runs'] = runs
        # number of total balls
        ann['balls'] = num_balls

        # run stats
        # ann['scored_reallylow'] += (0 < ann['runs'] <= num_balls/3)
        # ann['scored_low'] += (num_balls/3 < ann['runs'] <= 2*num_balls/3)
        # ann['scored_med'] += (2*num_balls/3 < ann['runs'] <= num_balls)
        # ann['scored_high'] += (num_balls < ann['runs'])
        if ann['num_out'] != 0:
            out = 'OUT'
        if ann['num_wide'] != 0:
            wide = 'WIDE'

        # bowler/batter stats
        # ann['p1_scored_more'] = appeared_more(ann['batters'], ann['batters'][0], [i == 'SCORED' for i in ann['scored']])
        # ann['p1_hit_more'] = appeared_more(ann['batters'], ann['batters'][0], [1] * num_balls)
        
        # information list in last index
        ann['stats'][0] = 'SCORED' if scored else 'NOT-SCORED'
        ann['stats'][1] = 'OUT' if out else 'NOT-OUT'
        ann['stats'][2] = 'WIDE' if wide else 'NOT-WIDE'

        #### adding the logical operator based queries
        # query_dict = {}
        if all_queries != None:
            for k in all_queries:
                trues = []
                if 'AND' in k:
                    all_ops = k.split(' AND ')
                    for j in all_ops:
                        if 'atleast' in j:
                            individual = j.split()
                            limit = int(individual[1])
                            atomic_event = individual[2][0]
                            num_occ = re.findall(atomic_event, ann['chains'])
                            if len(num_occ)>=limit:
                                trues.append(1)
                            else:
                                trues.append(0)
                        elif 'atmost' in j:
                            individual = j.split()
                            limit = int(individual[1])
                            atomic_event = individual[2][0]
                            num_occ = re.findall(atomic_event, ann['chains'])
                            if len(num_occ)<=limit:
                                trues.append(1)
                            else:
                                trues.append(0)
                        elif 'inrange' in j:
                            individual = j.split()
                            atomic_event = individual[0]
                            lower_limit = int(individual[2][1])
                            upper_limit = int(individual[3][0])
                            num_occ = re.findall(atomic_event, ann['chains'])
                            if len(num_occ) >= lower_limit and len(num_occ) <= upper_limit:
                                trues.append(1)
                            else:
                                trues.append(0)
                    final_res = all(trues)
                    query_dict[k] = int(final_res)
                elif 'OR' in k:
                    all_ops = k.split(' OR ')
                    for j in all_ops:
                        if 'atleast' in j:
                            individual = j.split()
                            limit = int(individual[1])
                            atomic_event = individual[2][0]
                            num_occ = re.findall(atomic_event, ann['chains'])
                            if len(num_occ)>=limit:
                                trues.append(1)
                            else:
                                trues.append(0)
                        elif 'atmost' in j:
                            individual = j.split()
                            limit = int(individual[1])
                            atomic_event = individual[2][0]
                            num_occ = re.findall(atomic_event, ann['chains'])
                            if len(num_occ)<=limit:
                                trues.append(1)
                            else:
                                trues.append(0)
                        elif 'inrange' in j:
                            individual = j.split()
                            atomic_event = individual[0]
                            lower_limit = int(individual[2][1])
                            upper_limit = int(individual[3][0])
                            num_occ = re.findall(atomic_event, ann['chains'])
                            if len(num_occ) >= lower_limit and len(num_occ) <= upper_limit:
                                trues.append(1)
                            else:
                                trues.append(0)
                    final_res = any(trues)
                    query_dict[k] = int(final_res)

        ann['logical_queries'] = query_dict
        # if ann['name'] == '2019_WC_final_Eng_vs_NZ':
        #     pdb.set_trace()

        combined_annots.append(ann)
        i += 1
    
    # print(i)
    # if ann['name'] == '2019_WC_final_Eng_vs_NZ':
    #     pdb.set_trace()
    return combined_annots


def combine_ann_overs_new(annotations, combine_len: int, all_queries=None):

    def appeared_more (player_list, p1, scored) -> bool:
        if len(player_list) != len(scored):
            raise ValueError('Batter list annotation and scored list not same length.') 
        m = 0 
        for i in range(len(player_list)):
            if scored[i] == 1:
                m += 1 if (p1 == player_list[i]) else -1
        return m > 0

    if len(annotations) < combine_len:
        raise ValueError('Not enough annotations for combine size')

    combined_annots = []


    # if all_queries!=None:
    #     all_query_keys = list(all_queries.keys())
    #     query_dict = dict.fromkeys(all_query_keys)

    i = 0
    # quite inefficient, but for purposes of density param, this will do.
    while i < len(annotations): 
        ann = {'name': '', 
               'overs': {}, 
               'start': 0, 
               'end': 0, 
               'batters': [],
               'bowlers': [], 
               'wide': [], 
               'out': [],
               'num_wide': 0, 
               'num_out': 0,
               'runs': 0, 
               'balls': 0,
               'num_boundaries': 0,
               'chains': [],
               'stats': ['','',''], 
               'scored': []}

        # if all_queries != None:
        #     ann['logical_queries'] = query_dict
        # if all_queries!=None:
        #     all_query_keys = list(all_queries.keys())
        #     query_dict = dict.fromkeys(all_query_keys)


        curr_over = prev_over = int(annotations[i]['overs'])
        runs, num_balls, j = 0, 0, 0
        scored, out, wide = False, False, False

        # chain events; order of importance goes out,wide,4/6 ball,scored,none
        to_append, chain = "", ""

        # start timestamp
        ann['start'] = annotations[i]['start']
        
        # combine certain number of overs
        while j < combine_len:
            to_append = "" # set string to nothing happened
            annot = annotations[i]

            # poorly structured, fix after
            if curr_over != prev_over:
                prev_over = curr_over
                j += 1
            if j >= combine_len:
                i -= 1
                break;

            # set name
            ann['name'] = annot['name'] 
            ann['overs'][annotations[i]['overs']] = annotations[i]['end']
            # ann['overs'].append(annotations[i]['overs'])
            # append bowler, batter
            ann['batters'].append(annotations[i]['batter'])
            ann['bowlers'].append(annotations[i]['bowler'])
            # sum balls and runs
            runs += annotations[i]['runs']

            # add scored balls
            to_append += (str(annotations[i]['runs']))
            # OR scored, not-out, not-wide
            ann['scored'].append(annotations[i]['stats'][0])
            ann['out'].append(annotations[i]['stats'][1])
            ann['wide'].append(annotations[i]['stats'][2])
            
            # total number of wide, out in game
            if annotations[i]['stats'][0] == 'SCORED':
                if not scored:
                    scored = True
            if annotations[i]['stats'][2] == 'WIDE': 
                to_append += "w"
                ann['num_wide'] += 1 
            if annotations[i]['stats'][1] == 'OUT': 
                to_append += "o"
                ann['num_out'] += 1 
            
            # number of boundaries
            ann['num_boundaries'] += (annotations[i]['runs'] - (1 if annotations[i]['stats'][2] == 'WIDE' else 0) == 4 or
            annotations[i]['runs'] - (1 if annotations[i]['stats'][2] == 'WIDE' else 0) >= 6)
            
            num_balls += 1
            chain += to_append + " "
            ann['chains'] = chain

            if i+1 < len(annotations) and j < combine_len:
                i += 1
                curr_over = int(annotations[i]['overs'])
            else:
                break
        

        # end timestamp
        ann['end'] = annotations[i]['end']
        # number of total runs
        ann['runs'] = runs
        # number of total balls
        ann['balls'] = num_balls

        # run stats
        # ann['scored_reallylow'] += (0 < ann['runs'] <= num_balls/3)
        # ann['scored_low'] += (num_balls/3 < ann['runs'] <= 2*num_balls/3)
        # ann['scored_med'] += (2*num_balls/3 < ann['runs'] <= num_balls)
        # ann['scored_high'] += (num_balls < ann['runs'])
        if ann['num_out'] != 0:
            out = 'OUT'
        if ann['num_wide'] != 0:
            wide = 'WIDE'

        # bowler/batter stats
        # ann['p1_scored_more'] = appeared_more(ann['batters'], ann['batters'][0], [i == 'SCORED' for i in ann['scored']])
        # ann['p1_hit_more'] = appeared_more(ann['batters'], ann['batters'][0], [1] * num_balls)
        
        # information list in last index
        ann['stats'][0] = 'SCORED' if scored else 'NOT-SCORED'
        ann['stats'][1] = 'OUT' if out else 'NOT-OUT'
        ann['stats'][2] = 'WIDE' if wide else 'NOT-WIDE'

        combined_annots.append(ann)
        i += 1
    
    # print(i)
    # if ann['name'] == '2019_WC_final_Eng_vs_NZ':
    #     pdb.set_trace()
    return combined_annots


def get_stats(num=1, combinations=None):
    path = './annotations/'
    stats = []
    stats_c = []

    
    # loop through all subdirectories
    suffixes = ['', '_day1', '_day2', '_day3', '_day4']
    dirs = glob.glob(path + '*/')
    for folder in dirs:
        json_name = folder.split('/')[-2]
        for suffix in suffixes:
            json_read_path = os.path.join(folder, json_name + suffix + '.json')
            if not os.path.exists(json_read_path):
                continue

            print('File: ', json_read_path)

            # load in json
            with open (json_read_path, 'r') as f:
                annots = json.load(f)
            stat = get_ann_stats(annots)
            # clean annotations before combining
            annots = clean_ann_before(annots)
            # name, over, start, end, runs, [info]
            annotations = combine_ann_overs_new(annots, combine_len=num)
            # clean annotations after combining
            annotations = clean_ann_after(annotations)

            stats.append(stat)
            stats_c.append(annotations)

    '''
    a_file = open(os.path.join(path,"stats.csv"), "w")
    keys = stats[0].keys()
    dict_writer = csv.DictWriter(a_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(stats)
    a_file.close()
    '''


    print('################## GETTING ALL THE STATS #########################')
    # stats_c = get_ann_chain_stats(stats_c, len(combinations[0]), combinations)
    op = 'atleast'
    op_new = ['atmost', 'atleast', 'atmost']
    combo = 'AND'
    chain_len = 5
    stats_c = get_ann_chain_stats_and_or(stats_c, chain_len, num, op, combo)
    # stats_c = get_ann_chain_stats_inrange(stats_c, chain_len, num, op, combo)
    # stats_c = get_ann_chain_stats_and_or_multi(stats_c, chain_len, num, op_new, combo)


    loc = os.path.join(path, str(chain_len) + "_" + op + "_" + combo)
    if not os.path.isdir(loc):
        os.makedirs(loc)

    b_file = open(os.path.join(path, str(chain_len) + "_" + op + "_" + combo, "stats_" + str(num) + "over.csv"), "w")
    # keys = set().union(*(d.keys() for d in sta    ts_c))
    # del stats_c['name'] # fix later
    x = dict([('name', 'ALL')] + sorted(stats_c[0].items(), key=lambda item: float(item[1]), reverse=True))
    keys = x.keys()
    stats_c[0]['name'] = 'AGGREGATE'

    dict_writer = csv.DictWriter(b_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(stats_c)
    b_file.close()

def main(num=1):
    global total_incorrect_order
    global total_time_over
    path = './annotations/'

    if num in [1,2]:
        query_loc = 'bucket_2_queries.json'
    elif num in [3,4]:
        query_loc = 'bucket_4_queries.json'
    elif num in [5,6]:
        query_loc = 'bucket_6_queries.json'
    elif num in [7,8]:
        query_loc = 'bucket_8_queries.json'
    elif num in [9,10]:
        query_loc = 'bucket_10_queries.json'

    with open(query_loc) as f:
        all_queries = json.load(f)
    
    # loop through all subdirectories
    suffixes = ['', '_day1', '_day2', '_day3', '_day4']
    dirs = glob.glob(path + '*/')
    for folder in dirs:
        json_name = folder.split('/')[-2]
        for suffix in suffixes:
            json_read_path = os.path.join(folder, json_name + suffix + '.json')
            if not os.path.exists(json_read_path):
                continue

            json_write_path_dict = os.path.join(folder, json_name + suffix + '_dict.json')
            json_write_path = os.path.join(folder, json_name + suffix + '_combined_' + str(num) + 'over.json')
            print('File: ', json_read_path)

            # load in json
            with open (json_read_path, 'r') as f:
                annots = json.load(f)

            # clean annotations before combining
            annots = clean_ann_before(annots)
            
            # name, over, start, end, runs, [info]
            annotations = combine_ann_overs(annots, combine_len=num, all_queries = all_queries)
            
            # clean annotations after combining
            # annotations = clean_ann_after(annotations)

            with open(json_write_path_dict, 'w') as json_file:
                json.dump(annots, json_file)

            with open(json_write_path, 'w') as json_file:
                json.dump(annotations, json_file)

    # print('Avg # incorrect order: ', total_incorrect_order / len(dirs))
    # print('Avg # >10 min snippets: ', total_time_over / len(dirs))

if __name__ == "__main__":
    # nums = [1,2,5,10]
    # for i in range(10):
    #     main(i+1)
    #     print('Done for over len ', i+1)

    # main(1)
    
    combos = generate_combinations(3)
    # get_stats(5, combos)
    # print(combos)
    for i in range(10):
        get_stats(i+1, combos)
        print('Done for over len ', i+1)