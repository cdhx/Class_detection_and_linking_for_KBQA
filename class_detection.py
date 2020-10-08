# -*- coding: utf-8 -*-
"""
Created on Tue Sep 29 18:53:56 2020

@author: Dell
"""


import json
import socket
import requests
from SPARQLWrapper import SPARQLWrapper, JSON
from all_func import *



dictionary={'people':'person','tv':'television','series':'show','organization':'organisation','movie':'film'}    

def relax_single_word_match_score(s1,type_split_lower):    
    '''每个候选设置得分，考虑了对of停用词的处理'''
    def lemma_nessary(s1_split,s2_split,match_num,have_stop_word_match):
        for s2i in s2_split:
            for s1i in s1_split:           
                s2i.replace('-','').strip()
                #方案一，匹配不上再做还原
                if s2i==s1i:
                    if s2i in stop_word_list:
                        have_stop_word_match += 1
                    else:
                        match_num += 1
                else:
                    s1i_lemma=get_lemma(s1i)                                
                    s2i_lemma=get_lemma(s2i)
                    if s2i_lemma==s1i_lemma:
                        if s2i_lemma in stop_word_list:
                            have_stop_word_match+=1
                        else:
                            match_num+=1

                    else:#还不行，加入词典
                        if s1i_lemma in list(dictionary.keys()):
                            if dictionary[s1i_lemma]==s2i_lemma:
                                if s2i_lemma in stop_word_list:
                                    have_stop_word_match += 1
                                else:
                                    match_num += 1
                        
                            
                            
                            
        return match_num,have_stop_word_match
   
    def lemma_all(s1_split,s2_split,match_num,have_stop_word_match):
        for s2i in s2_split:
            for s1i in s1_split:           
                s2i.replace('-','').strip()
                #方案二，一律做还原
                s1i_lemma=get_lemma(s1i)                                
                s2i_lemma=get_lemma(s2i)
                if s2i_lemma==s1i_lemma:
                    if s2i_lemma in stop_word_list:
                        have_stop_word_match += 1
                    else:
                        match_num += 1
                else:#还不行，加入词典
                    if s1i_lemma in list(dictionary.keys()):
                        if dictionary[s1i_lemma]==s2i_lemma:
                            if s2i_lemma in stop_word_list:
                                have_stop_word_match += 1
                            else:
                                match_num += 1
                                 
                
        return match_num,have_stop_word_match
    

    match_func=lemma_nessary
    
    
    s1.replace('?','').replace('-','').strip()
    result_score={}

    for s2 in type_split_lower:
        s1_split=s1.strip().split(' ')
        s2_split=s2.strip().split(' ')        
        s1_split=list(map(lambda x:x.strip(),s1_split))
        s2_split=list(map(lambda x:x.strip(),s2_split))
        match_num=0
        stop_word_list=['of','one','player']
        have_stop_word_match=0
        target_num=len(s2_split)
        
        match_num,have_stop_word_match=match_func(s1_split, s2_split,match_num,have_stop_word_match) 
                        
        if match_num>0:
            match_num+=have_stop_word_match
                    
        #计入统计
        if match_num==target_num and target_num==3:
            result_score[s2]=6
        elif match_num==target_num and target_num==2:                
            result_score[s2]=5
        elif match_num==target_num and target_num==1:
            result_score[s2]=4
        elif match_num==2 and target_num==3:
            result_score[s2]=3
        elif match_num==1 and target_num==3:
            result_score[s2]=2
        elif match_num==1 and target_num==2:
            result_score[s2]=1

    result_score=sorted(result_score.items(),key=lambda item:item[1],reverse=True)
    
    return result_score
    

def NVP_match_result_merge(all_NVP_match_result):
    '''多个NVP的匹配结果合并去重排序加limit'''
    result={}
    for item in all_NVP_match_result:
        if item[0] in result.keys():
            if item[1]>result[item[0]]:
                result[item[0]]=item[1]
        else:
            result[item[0]]=item[1]
    result=sorted(result.items(),key=lambda item:item[1],reverse=True)
    return result
        
        
def main(edg,max_cand_num=5):
    '''主函数，对任意edg进行class链接'''

    #获取一个问句所有NVP
    NVP=[]
    nodes=edg['nodes']
    for node in nodes:
        if node['nodeType']==4:
            str1=node['str']
            if '#ent' not in str1:
                NVP.append(str1.strip())
    if len(NVP)==0:return []
    #获取一个问句的三元组列表
    sparql=edg['sparql_query']
    sparql=sparql[sparql.find('{')+1:sparql.find('}')]
    triple_list=sparql.split(' . ')
    #每个三元组
    for x in triple_list:
        #防止有的type关系混着用
        if 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' in x or 'rdf:type' in x or ' a ' in x:
            match_result=sum(list(map(lambda _x:relax_single_word_match_score(_x, type_split_lower),NVP)),[])#首先计算所有NVP的匹配结果，用_x避免混淆
            match_result=NVP_match_result_merge(match_result)#获取合并重排序的结果和分数
            match_result=list(map(lambda x: x[0],match_result))[:max_cand_num]#获取匹配结果，不要分数
            result=list(map(lambda x:content_link_map[x],match_result))

    return result

def CL(NVP, max_cand_num=5):
    '''主函数，对任意edg进行class链接'''
    file = open('content_link_map.txt', 'r')
    js = file.read()
    content_link_map = json.loads(js)
    file.close()

    file = open('type_split_lower.txt', 'r')
    type_split_lower = eval(file.read())
    file.close()

    match_result = relax_single_word_match_score(NVP, type_split_lower)# 首先计算所有NVP的匹配结果，用_x避免混淆
    match_result = NVP_match_result_merge(match_result)  # 获取合并重排序的结果和分数
    match_result = list(map(lambda x: x[0], match_result))[:max_cand_num]  # 获取匹配结果，不要分数
    result = list(map(lambda x: content_link_map[x], match_result))
    return result


if __name__ == '__main__':

    max_cand_num=5#最多返回多少个候选
    print('Linking result:',CL('school is good'))
