#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np
from tqdm import tqdm
import os
from collections import defaultdict  
import math  
import json
from sys import stdout
import pickle


# In[ ]:





def ReComputeSim(sim_cor,candidate_item_list,interacted_items,item_weight_dict,flag=False):
    
    sim_list = []
    for j in candidate_item_list:
        sim_tmp = 0
        for loc, i in enumerate(interacted_items):  
        #Just for RA gernerated by offline
            if i not in sim_cor or j not in sim_cor[i]:
                continue
            if i in item_weight_dict:
                sim_tmp += sim_cor[i][j][0] * (0.7**loc) * item_weight_dict[i] if flag else sim_cor[i][j] * (0.7**loc) * item_weight_dict[i]
            else:
                sim_tmp += sim_cor[i][j][0] * (0.7**loc) * 0.5 if flag else sim_cor[i][j] * (0.7**loc) * 0.5
        
        sim_list.append(sim_tmp)
            
    return sim_list


# In[ ]:


file_name = 'recall_0531_addsim'

offline = pd.read_csv('./user_data/model_1/new_recall/' + file_name + '.csv')

now_phase = 9


train_path = './user_data/model_1/'  
test_path = './user_data/model_1/'
header = 'model_1'
out_path = './user_data/model_1/new_similarity/'

recom_item = []  

whole_click = pd.DataFrame()  


user_id_list = []
item_id_list = []


ra_sim_list = []
aa_sim_list = []


    
for c in range(now_phase + 1):  
    print('phase:', c)  
    click_train = pd.read_csv(train_path + header + '_train_click_{}_time.csv'.format(c))  
    click_test = pd.read_csv(test_path +  header + '_test_click_{}_time.csv'.format(c))  
    click_query = pd.read_csv(test_path +  header + '_test_qtime_{}_time.csv'.format(c)) 


    click_train['datetime'] = pd.to_datetime(click_train['datetime'])
    click_test['datetime'] = pd.to_datetime(click_test['datetime'])
    click_query['datetime'] = pd.to_datetime(click_query['datetime'])



    click_train['timestamp'] = click_train['datetime'].dt.day + ( click_train['datetime'].dt.hour + 
                          (click_train['datetime'].dt.minute + click_train['datetime'].dt.second/60)/float(60) )/float(24)

    click_test['timestamp'] = click_test['datetime'].dt.day + ( click_test['datetime'].dt.hour + 
                          (click_test['datetime'].dt.minute + click_test['datetime'].dt.second/60)/float(60) )/float(24)

    click_query['timestamp'] = click_query['datetime'].dt.day + ( click_query['datetime'].dt.hour + 
                          (click_query['datetime'].dt.minute + click_query['datetime'].dt.second/60)/float(60) )/float(24)


    all_click = click_train.append(click_test)  
        

    with open(out_path+'user2item_new'+str(c)+'.pkl','rb') as f:
        user_item_tmp = pickle.load(f)         
        
    with open(out_path+'RA_P'+str(c)+'_new.pkl','rb') as f:
         RA_sim_list_new = pickle.load(f)  
    
    
    for i, row in click_query.iterrows():
        offline_tmp = offline[offline['user_id']==row['user_id']]
        candidate_item_list = list(offline_tmp['item_id'])
        
        time_min = min(all_click['timestamp'])
        time_max = row['timestamp']

        df_tmp = all_click[all_click['user_id']==row['user_id']]
        df_tmp = df_tmp.reset_index(drop=True)
        df_tmp['weight'] = 1 - (time_max-df_tmp['timestamp']+0.01) / (time_max-time_min+0.01)
        item_weight_dict = dict(zip(df_tmp['item_id'], df_tmp['weight']))

        interacted_items = user_item_tmp[row['user_id']]
        interacted_items = interacted_items[::-1]
        
        sim_list_tmp = ReComputeSim(RA_sim_list_new,candidate_item_list,interacted_items,item_weight_dict)
        ra_sim_list += sim_list_tmp    
        
        item_id_list += candidate_item_list
        user_id_list += [row['user_id'] for x in candidate_item_list]        
        
    RA_sim_list_new = []        

    
        
    with open(out_path+'AA_P'+str(c)+'_new.pkl','rb') as f:
         AA_sim_list_new = pickle.load(f)  
    
    
    for i, row in click_query.iterrows():
        offline_tmp = offline[offline['user_id']==row['user_id']]
        candidate_item_list = list(offline_tmp['item_id'])
        
        time_min = min(all_click['timestamp'])
        time_max = row['timestamp']

        df_tmp = all_click[all_click['user_id']==row['user_id']]
        df_tmp = df_tmp.reset_index(drop=True)
        df_tmp['weight'] = 1 - (time_max-df_tmp['timestamp']+0.01) / (time_max-time_min+0.01)
        item_weight_dict = dict(zip(df_tmp['item_id'], df_tmp['weight']))

        interacted_items = user_item_tmp[row['user_id']]
        interacted_items = interacted_items[::-1]
        
        sim_list_tmp = ReComputeSim(AA_sim_list_new,candidate_item_list,interacted_items,item_weight_dict)
        aa_sim_list += sim_list_tmp
         
    
    AA_sim_list_new = []   

    
    


# In[ ]:





# In[ ]:


offline.shape


# In[ ]:





# In[ ]:





# In[ ]:


sim_df = pd.DataFrame()
sim_df['user_id'] = user_id_list
sim_df['item_id'] = item_id_list
sim_df['ra_sim'] = ra_sim_list
sim_df['aa_sim'] = aa_sim_list


# In[ ]:


sim_df.shape


# In[ ]:


offline = offline.merge(sim_df,on=['user_id','item_id'])


# In[ ]:





# In[ ]:


offline.to_csv('./user_data/model_1/new_recall/'+ file_name + '_addAA_RA.csv',index=False)


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




