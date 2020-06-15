#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
from tqdm import tqdm
import os
from collections import defaultdict  
import math  
import json
from sys import stdout
import pickle
import time
import gc


# In[2]:


def get_predict(df, pred_col, top_fill, ranknum):  
    top_fill = [int(t) for t in top_fill.split(',')]  
    scores = [-1 * i for i in range(1, len(top_fill) + 1)]  
    ids = list(df['user_id'].unique())  
    fill_df = pd.DataFrame(ids * len(top_fill), columns=['user_id'])  
    fill_df.sort_values('user_id', inplace=True)  
    fill_df['item_id'] = top_fill * len(ids)  
    fill_df[pred_col] = scores * len(ids)  
    df = df.append(fill_df)  
    df.sort_values(pred_col, ascending=False, inplace=True)  
    df = df.drop_duplicates(subset=['user_id', 'item_id'], keep='first')  
    df['rank'] = df.groupby('user_id')[pred_col].rank(method='first', ascending=False)  
    df = df[df['rank'] <= ranknum]  
    df = df.groupby('user_id')['item_id'].apply(lambda x: ','.join([str(i) for i in x])).str.split(',', expand=True).reset_index()  
    return df  


# In[3]:


def recommend(sim_item_corr, user_item_dict, user_id, times, item_dict, item_time_dict, top_k, item_num):
    '''
    input:item_sim_list, user_item, uid, 500, 50
    # 用户历史序列中的所有商品均有关联商品,整合这些关联商品,进行相似性排序
    '''
    rank = {}
    interacted_items = user_item_dict[user_id]
    interacted_items = interacted_items[::-1]
    times = times[::-1]
    t0 = times[0]
    for loc, i in enumerate(interacted_items):
        for j, wij in sorted(sim_item_corr[i].items(), key=lambda d: d[1]['sim'], reverse=True)[0:top_k]:
            if j not in interacted_items:
                rank.setdefault(j, {'sim': 0,
                                        'item_cf': 0,
                                        'item_cf_weighted': 0,
                                        'time_diff': np.inf,
                                        'loc_diff': np.inf,
                                        # Some feature generated by recall
                                        'time_diff_recall': np.inf,
                                        'time_diff_recall_1': np.inf,
                                        'loc_diff_recall': np.inf,
                                        # Nodesim and Deepsim
                                          'node_sim_max': -1e8,
                                          'node_sim_sum':0,
                                          'deep_sim_max': -1e8,
                                          'deep_sim_sum':0,
                                          })
                t1 = times[loc]
                t2 = item_time_dict[j][0]
                delta_t1 = abs(t0 - t1) * 650000
                delta_t2 = abs(t0 - t2) * 650000
                alpha = max(0.2, 1 / (1 + item_dict[j]))
                beta = max(0.5, (0.9 ** loc))
                theta = max(0.5, 1 / (1 + delta_t1))
                gamma = max(0.5, 1 / (1 + delta_t2))

                rank[j]['sim'] += wij['sim'] * (alpha ** 2) * (beta) * (theta ** 2) * gamma
                rank[j]['item_cf'] += wij['item_cf']
                rank[j]['item_cf_weighted'] += wij['item_cf_weighted']
                
                if wij['time_diff'] < rank[j]['time_diff']:
                    rank[j]['time_diff'] = wij['time_diff']
                if wij['loc_diff'] < rank[j]['loc_diff']:
                    rank[j]['loc_diff'] = wij['loc_diff']
                if delta_t1 < rank[j]['time_diff_recall']:
                    rank[j]['time_diff_recall'] = delta_t1
                if delta_t2 < rank[j]['time_diff_recall_1']:
                    rank[j]['time_diff_recall_1'] = delta_t2
                if loc < rank[j]['loc_diff_recall']:
                    rank[j]['loc_diff_recall'] = loc
                    
                if wij['node_sim_max'] > rank[j]['node_sim_max']:
                    rank[j]['node_sim_max'] = wij['node_sim_max']
                rank[j]['node_sim_sum'] += wij['node_sim_sum'] / wij['item_cf']
                
                if wij['deep_sim_max'] > rank[j]['deep_sim_max']:
                    rank[j]['deep_sim_max'] = wij['deep_sim_max']
                rank[j]['deep_sim_sum'] += wij['deep_sim_sum'] / wij['item_cf']
                
    return sorted(rank.items(), key=lambda d: d[1]['sim'], reverse=True)[:item_num]


# In[4]:


now_phase = 9

offline = "./user_data/dataset/"
header = 'underexpose'
input_path = './user_data/dataset/new_similarity/'
output_path = './user_data/dataset/new_recall/'


# In[5]:


# recom_item = []  

# for c in range(now_phase + 1):  
#     a = time.time()

#     print('phase:', c)  
    
#     with open(input_path+'itemCF_new'+str(c)+'.pkl','rb') as f:
#         item_sim_list = pickle.load(f)    

#     with open(input_path+'user2item_new'+str(c)+'.pkl','rb') as f:
#         user_item = pickle.load(f)                  
              
#     with open(input_path+'item2cnt_new'+str(c)+'.pkl','rb') as f:
#         item_dic = pickle.load(f) 

#     with open(input_path+'userTime'+str(c)+'.pkl','rb') as f:
#         user_time_dict = pickle.load(f)         
        
#     with open(input_path+'itemTime'+str(c)+'.pkl','rb') as f:
#         item_time_dict = pickle.load(f)          
        
#     qtime_test = pd.read_csv(offline + header + '_test_qtime-{}.csv'.format(c), header=None,
#                               names=['user_id', 'item_id', 'time'])
    
    
#     for user in tqdm(qtime_test['user_id'].unique()):
#         if user in user_time_dict:
#             times = user_time_dict[user]
#             rank_item = recommend(item_sim_list, user_item, user, times, item_dic, item_time_dict, 500, 500)
#             for j in rank_item:
#                 recom_item.append([user, int(j[0])] + list(j[1].values()))      
#     gc.collect()
file = open(input_path + 'recom_item.pkl', 'rb')
recom_item = pickle.load(file)
file.close()


# In[6]:


for phase in range(now_phase + 1):
    a = time.time()
    history_list = []
    for i in range(now_phase + 1):
        click_train = pd.read_csv(offline + header + '_train_click-{}.csv'.format(i), header=None,
                                  names=['user_id', 'item_id', 'time'])
        click_test = pd.read_csv(offline + header + '_test_click-{}.csv'.format(i), header=None,
                                 names=['user_id', 'item_id', 'time'])

        all_click = click_train.append(click_test)
        history_list.append(all_click)

    # qtime_test = pd.read_csv(offline + 'offline_test_qtime-{}.csv'.format(phase), header=None,
    #                          names=['user_id', 'item_id', 'time'])
    click_test = pd.read_csv(offline + header+ '_test_click-{}.csv'.format(phase), header=None,
                             names=['user_id', 'item_id', 'time'])
    print(click_test['user_id'].nunique())

    print('phase:', phase)
    time_diff = max(history_list[now_phase]['time']) - min(history_list[0]['time'])
    for i in range(phase + 1, now_phase + 1):
        history_list[i]['time'] = history_list[i]['time'] - time_diff

    whole_click = pd.DataFrame()
    for i in range(now_phase + 1):
        whole_click = whole_click.append(history_list[i])


    whole_click = whole_click.drop_duplicates(subset=['user_id', 'item_id', 'time'], keep='last')
    whole_click = whole_click.sort_values('time')
    whole_click = whole_click.reset_index(drop=True)


# In[7]:


def phase_predict(df, pred_col, top_fill, topk=50):
    """recom_df, 'sim', top50_click, "click_valid"
    """
    top_fill = [int(t) for t in top_fill.split(',')]
    top_fill = top_fill[:topk]
    scores = [-1 * i for i in range(1, len(top_fill) + 1)]
    ids = list(df['user_id'].unique())
    fill_df = pd.DataFrame(ids * len(top_fill), columns=['user_id'])
    fill_df.sort_values('user_id', inplace=True)
    fill_df['item_id'] = top_fill * len(ids)
    fill_df[pred_col] = scores * len(ids)
    df = df.append(fill_df)
    df.sort_values(pred_col, ascending=False, inplace=True)
    df = df.drop_duplicates(subset=['user_id', 'item_id'], keep='first')
    df['rank'] = df.groupby('user_id')[pred_col].rank(method='first', ascending=False)
    df.sort_values("rank", inplace=True)
    df = df[df["rank"] <= topk]
    df = df.groupby('user_id')['item_id'].apply(lambda x: ','.join([str(i) for i in x])).str.split(',',
                                                                                                   expand=True).reset_index()
    return df


# In[8]:


# find most popular items
top50_click = whole_click['item_id'].value_counts().index[:500].values
top50_click = ','.join([str(i) for i in top50_click])

recom_df = pd.DataFrame(recom_item, columns=['user_id', 'item_id', 'sim'] + ['feature_' + str(x) for x in range(len(recom_item[0]) - 3)])
result = phase_predict(recom_df, 'sim', top50_click, 50)
result['user_id'] = result['user_id'].astype(int)
result.to_csv('Recall_0531.csv', index=False, header=None)        


# In[9]:


import datetime


# In[10]:


# the higher scores, the better performance
def evaluate_each_phase(predictions, answers, rank_num):
    list_item_degress = []
    for user_id in answers:
        item_id, item_degree = answers[user_id]
        list_item_degress.append(item_degree)
    list_item_degress.sort()
    median_item_degree = list_item_degress[len(list_item_degress) // 2]

    num_cases_full = 0.0
    ndcg_50_full = 0.0
    ndcg_50_half = 0.0
    num_cases_half = 0.0
    hitrate_50_full = 0.0
    hitrate_50_half = 0.0
    for user_id in answers:
        item_id, item_degree = answers[user_id]
        rank = 0
        while rank < rank_num and predictions[user_id][rank] != item_id:
            rank += 1
        num_cases_full += 1.0
        if rank < rank_num:
            ndcg_50_full += 1.0 / np.log2(rank + 2.0)
            hitrate_50_full += 1.0
        if item_degree <= median_item_degree:
            num_cases_half += 1.0
            if rank < rank_num:
                ndcg_50_half += 1.0 / np.log2(rank + 2.0)
                hitrate_50_half += 1.0
    ndcg_50_full /= num_cases_full
    hitrate_50_full /= num_cases_full
    ndcg_50_half /= num_cases_half
    hitrate_50_half /= num_cases_half
    
    print([ndcg_50_full, ndcg_50_half,
                     hitrate_50_full, hitrate_50_half])
    
    return np.array([ndcg_50_full, ndcg_50_half,
                     hitrate_50_full, hitrate_50_half], dtype=np.float32)

# submit_fname is the path to the file submitted by the participants.
# debias_track_answer.csv is the standard answer, which is not released.
def evaluate(stdout, submit_fname,
             answer_fname='debias_track_answer.csv', rank_num=50, current_time=None):
    schedule_in_unix_time = [
        0,  # ........ 1970-01-01 08:00:00 (T=0)
        1586534399,  # 2020-04-10 23:59:59 (T=1)
        1587139199,  # 2020-04-17 23:59:59 (T=2)
        1587743999,  # 2020-04-24 23:59:59 (T=3)
        1588348799,  # 2020-05-01 23:59:59 (T=4)
        1588953599,  # 2020-05-08 23:59:59 (T=5)
        1589558399,  # 2020-05-15 23:59:59 (T=6)
        1590163199,  # 2020-05-22 23:59:59 (T=7)
        #1589558399,
        1590767999,  # 2020-05-29 23:59:59 (T=8)
        1591372799  # .2020-06-05 23:59:59 (T=9)
    ]
    assert len(schedule_in_unix_time) == 10
    for i in range(1, len(schedule_in_unix_time) - 1):
        # 604800 == one week
        assert schedule_in_unix_time[i] + 604800 == schedule_in_unix_time[i + 1]

    if current_time is None:
        current_time = int(time.time())
    print('current_time:', current_time)
    print('date_time:', datetime.datetime.fromtimestamp(current_time))
    current_phase = 0
    while (current_phase < 9) and (
            current_time > schedule_in_unix_time[current_phase + 1]):
        current_phase += 1
    print('current_phase:', current_phase)

    try:
        answers = [{} for _ in range(10)]
        with open(answer_fname, 'r') as fin:
            for line in fin:
                line = [int(x) for x in line.split(',')]
                phase_id, user_id, item_id, item_degree = line
                assert user_id % 11 == phase_id
                # exactly one test case for each user_id
                answers[phase_id][user_id] = (item_id, item_degree)
    except Exception as _:
        print( 'server-side error: answer file incorrect\n')
        return -1

    try:
        predictions = {}
        with open(submit_fname, 'r') as fin:
            for line in fin:
                line = line.strip()
                if line == '':
                    continue
                line = line.split(',')
                user_id = int(line[0])
                if user_id in predictions:
                    print('submitted duplicate user_ids \n')
                    return -1
                item_ids = [int(i) for i in line[1:]]
                if len(item_ids) != rank_num:
                    print('each row need have 50 items \n')
                    return -1
                if len(set(item_ids)) != rank_num:
                    print('each row need have 50 DISTINCT items \n')
                    return -1
                predictions[user_id] = item_ids
    except Exception as _:
        print('submission not in correct format \n')
        return -1

    scores = np.zeros(4, dtype=np.float32)

    # The final winning teams will be decided based on phase T=7,8,9 only.
    # We thus fix the scores to 1.0 for phase 0,1,2,...,6 at the final stage.
    #if current_phase >= 7:  # if at the final stage, i.e., T=7,8,9
    #    scores += 7.0  # then fix the scores to 1.0 for phase 0,1,2,...,6
    #phase_beg = (7 if (current_phase >= 7) else 0)
    phase_beg = 0
    phase_end = current_phase + 1
    for phase_id in range(phase_beg, phase_end):
        for user_id in answers[phase_id]:
            if user_id not in predictions:
                print('user_id %d of phase %d not in submission' % (user_id, phase_id))
                return -1
        try:
            # We sum the scores from all the phases, instead of averaging them.
            scores += evaluate_each_phase(predictions, answers[phase_id], rank_num)
        except Exception as _:
            print('error occurred during evaluation')
            return -1

    return [float(scores[0]),float(scores[0]),float(scores[1]),float(scores[2]),float(scores[3])]


# In[11]:


recom_df[['user_id','item_id']].to_csv(output_path + 'user_item_index.csv', index=False)


# In[12]:


recom_df.to_csv(output_path + 'recall_0531.csv', index=False)


# In[13]:


output_path + 'recall_0531.csv'


# In[14]:


from sys import stdout
print(evaluate(stdout,'Recall_0531.csv',
             answer_fname=offline + header + '_debias_track_answer.csv', rank_num=50))


#         current_time: 1590673576
#         date_time: 2020-05-28 21:46:16
#         current_phase: 6
#         [0.07291776530294389, 0.04257302451332752, 0.16795865633074936, 0.10839160839160839]
#         [0.07522970326234413, 0.047286878349803496, 0.1778875849289685, 0.12471655328798185]
#         [0.08768431272730617, 0.05220432316374826, 0.2040429564118762, 0.13366960907944514]
#         [0.08137267931092253, 0.04650284552993235, 0.18584070796460178, 0.10888610763454318]
#         [0.086082070609559, 0.06099578564127202, 0.20061919504643963, 0.14116251482799524]
#         [0.08282023366562385, 0.05404211657982558, 0.18724400234055003, 0.1210710128055879]
#         [0.08625658967639374, 0.05129722585118765, 0.19410745233968804, 0.12543153049482164]
#         [0.5723633170127869, 0.5723633170127869, 0.3549021780490875, 1.3177005052566528, 0.8633289337158203]

#         current_time: 1590730998
#         date_time: 2020-05-29 13:43:18
#         current_phase: 6
#         [0.07336197799145278, 0.04333070177814886, 0.17118863049095606, 0.11188811188811189]
#         [0.07551020515190006, 0.047111743016730066, 0.17974058060531192, 0.12698412698412698]
#         [0.0877367887009624, 0.052890596296164785, 0.2040429564118762, 0.13619167717528374]
#         user_id 3 of phase 3 not in submission