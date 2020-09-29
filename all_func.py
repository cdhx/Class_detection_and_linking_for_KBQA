# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 15:08:16 2020

@author: njucsxh
"""
from SPARQLWrapper import SPARQLWrapper, JSON    
import re
import numpy as np
import pandas as pd
import json
import socket
from pandas.io.json import json_normalize
import json
import requests
from itertools import chain
from nltk.corpus import wordnet as wn
from collections import Counter
from collections import defaultdict
import nltk
from nltk.stem import WordNetLemmatizer
from nltk import word_tokenize, pos_tag
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from tqdm import tqdm
class RegexDict(dict):
    import re
    def __init__(self, *args, **kwds):
        self.update(*args, **kwds)

    def __getitem__(self, required):
        for key in dict.__iter__(self):
            if self.re.match(key, required):
                return dict.__getitem__(self, key)
        return dict.__getitem__(self, key) # redundancy but it can handle exceptions.

pre_map={
 'prop': '<http://dbpedia.org/property/>',
 'owl': '<http://www.w3.org/2002/07/owl#>',
 'dbp': '<http://dbpedia.org/property/>',
 'dct': '<http://purl.org/dc/terms/>',
 'res': '<http://dbpedia.org/resource/>',
 'dbo': '<http://dbpedia.org/ontology/>',
 'skos': '<http://www.w3.org/2004/02/skos/core#>',
 'db': '<http://dbpedia.org/>',
 'yago': '<http://dbpedia.org/class/yago/>',
 'onto': '<http://dbpedia.org/ontology/>',
 #'xsd': '<http://www.w3.org/2001/XMLSchema#>',#注释掉它，比较特殊
 'rdfs': '<http://www.w3.org/2000/01/rdf-schema#>',
 'foaf': '<http://xmlns.com/foaf/0.1/>',
 'dbr': '<http://dbpedia.org/resource/>',
 'dbc': '<http://dbpedia.org/resource/Category:>',
 'dbpedia2': '<http://dbpedia.org/property/>'
}

map_pre = RegexDict({
'<http://dbpedia.org/>':'db',
'<http://dbpedia.org/class/yago/.*?>':'yago',
'<http://dbpedia.org/ontology/.*?>':'dbo',
'<http://dbpedia.org/property/.*?>':'dbp',
'<http://dbpedia.org/resource/.*?>':'dbr',
'<http://dbpedia.org/resource/Category:>':'dbc',
'<http://purl.org/dc/terms/.*?>':'dct',
'<http://www.w3.org/1999/02/22-rdf-syntax-ns#>':'rdf',
'<http://www.w3.org/2000/01/rdf-schema#>':'rdfs',
#'<http://www.w3.org/2001/XMLSchema#>':'xsd',
'<http://www.w3.org/2002/07/owl#>':'owl',
'<http://xmlns.com/foaf/0.1/>':'foaf',
'<http://www.w3.org/2004/02/skos/core#>':'skos'
 })
#返回最长子串及其长度
def find_lcsubstr(s1, s2_list): 
    '''
    返回s1在s2_list所有候选中的最长字串
    
    Args:
        s1:原词 str
        s2_list:可以匹配的选项 list
        
    Reture:最长字串
    '''
    curr_len=0
    substr=''
    for s2 in s2_list:
        m=[[0 for i in range(len(s2)+1)]  for j in range(len(s1)+1)]  #生成0矩阵，为方便后续计算，比字符串长度多了一列
        mmax=0   #最长匹配的长度
        p=0  #最长匹配对应在s1中的最后一位
        for i in range(len(s1)):
    	    for j in range(len(s2)):
    		    if s1[i]==s2[j]:
    			    m[i+1][j+1]=m[i][j]+1
    			    if m[i+1][j+1]>mmax:
    				    mmax=m[i+1][j+1]
    				    p=i+1
        if mmax>curr_len:
            substr=s1[p-mmax:p]
            curr_len=mmax
    return substr   #返回最长子串及其长度
#把一个字符串根据首字母大写分成空格分开的形式
#FootballPlayer -> football player
def splitByTitle(string):
    '''
    把一个字符串根据首字母大写分成用空格分开的形式
    
    FootballPlayer -> football player
    '''
    split=[]
    for i in range(len(string)-1,-1,-1):
        if string[i].istitle():
            split.append(string[i:].lower())
            string=string[:i]
    split.reverse()            
    return ' '.join(split)

def get_host_ip():
    """查询本机ip地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip
def answer_convert(item_answer):
    '''解析query函数得到的答案，或用于QALD数据集的答案提取'''
    if 'boolean' in item_answer.keys():
        at='boolean'
    else:
        at= item_answer['head']['vars'][0]
    answer=[]
    if at=='boolean':
        answer.append(item_answer['boolean'])        
    else:
        for cand in item_answer['results']['bindings']:
            if at=='date':
                answer.append(cand['date']['value'])
            elif at=='number':
                answer.append(cand['c']['value'])                
            elif at=='resource' or at=='uri':
                answer.append(cand['uri']['value'])
            elif at=='string':
                answer.append(cand['string']['value'])
            elif at=='callret-0':
                answer.append(cand['callret-0']['value'])
            else:#貌似都是这个套路，不知道还有什么类型
                answer.append(cand[at]['value'])
    return answer

def string_simi(nlp,kbp,limit=1):    #kbp不去前缀和只有内容都可以处理
    '''计算字面相似度,返回kbp中相似度最高的
    
    Arg:
        nlp:str
        kbp:list
        limit:返回多少个结果,默认为一
        '''
    import Levenshtein
    ratio=[]#nlp是一个NL单词，kbp是一个candidate list
    for kbcand in kbp:# 一个NL词和所有kb中的比较,kbp是去了前缀的
        str1 = nlp
        #如果有前缀，那么最后一个/#之后的就是内容，最后一个字符应该是>，去掉；如果没有前缀，搜索不到结果=-1再+1=0，也没问题
        #可以直接find有没有<和>判断是不是完整的uri，完整的用rfind去掉前缀，不完整的只有内容的全取        
        if kbcand.find('<')!=-1 and kbcand.find('>')!=-1:#<http:>格式
            str2=kbcand[max(kbcand.rfind('/'),kbcand.rfind('#'))+1:-1] 
        elif kbcand.find('http:')!=-1:#http:格式
            str2=kbcand[max(kbcand.rfind('/'),kbcand.rfind('#'))+1:] 
        else:#没有前缀格式
            str2=kbcand
        # 计算莱文斯坦比
        sim = Levenshtein.ratio(str1, str2)
        ratio.append(sim) 
        # 计算jaro距离
        #sim = Levenshtein.jaro(str1, str2 )
        #ratio.append(sim) 
        #  Jaro–Winkler距离
        #sim = Levenshtein.jaro_winkler(str1 , str2 )            
        #ratio.append(sim)
    #print(nlp,kbp[ratio.index(max(ratio))],max(ratio))#nl,kb最好的,对应的相似度
    #prefix='http://dbpedia.org/ontology/'
    if limit==1:
        return  kbp[ratio.index(max(ratio))]#最好的,不加前缀
    else:
        result=[]
        for i in range(min(limit,len(kbp))):
            result.append(kbp[ratio.index(max(ratio))])
            ratio[ratio.index(max(ratio))]=0
        return result

def get_content(uri):
    '''#给任意形式，获得content，dbo:content,http:/.../content,<http:/.../content>'''
    uri=uri.replace('<','')
    uri=uri.replace('>','')
    if 'http://' in uri:
        content=uri[max(uri.rfind('/'),uri.rfind('#'))+1:]#获取内容                    
        return content.strip()
    elif ':' in uri:#不严谨，有的content里面也有:，导致query里dbo:abd:ab会报错
        content=uri[uri.rfind(':')+1:]#获取内容
        return content.strip()
    else:
        content=uri
    return content.strip()    
def get_plural_multi_word(word):
    '''取复数形式,可以处理多个词'''
    import inflect
    p = inflect.engine()
    if len(word.split(' '))==1:
        word=word.lower() #小写，大写可能还原不了 比如Specialities
        word=p.plural(word)
    else:
        process_word=word.split(' ')[-1]
        process_word=process_word.lower() #小写，大写可能还原不了 比如Specialities
        process_word=p.plural(process_word)
        word=' '.join(word.split(' ')[:-1])+' '+process_word    
    return word
def get_lemma_multi_word(word):
    '''可以处理多个单词，最后一个单词为复数的情况，空格分割'''
    wnl = WordNetLemmatizer()  #还原器
    if len(word.split(' '))==1:
        word=word.lower().strip() #小写，大写可能还原不了 比如Specialities
        tag = pos_tag([word])     # 获取单词词性        
        wordnet_pos = get_wordnet_pos_normalize(tag[0][1]) or wordnet.NOUN#忘了这个or什么意思了，真的有找不到词性的情况？
        return wnl.lemmatize(tag[0][0], pos=wordnet_pos) # 词形还原
    else:#多个词的情况
        process_word=word.split(' ')[-1]
        process_word=process_word.lower() #小写，大写可能还原不了 比如Specialities
        tag = pos_tag([process_word])
        wordnet_pos = get_wordnet_pos_normalize(tag[0][1]) or wordnet.NOUN
        return ' '.join(word.split(' ')[:-1])+' '+wnl.lemmatize(tag[0][0], pos=wordnet_pos) # 词形还原    
def get_lemma(word):
    #wordnet标准化（词形还原）
    wnl = WordNetLemmatizer()  #还原器
    word=word.lower().strip() #小写，大写可能还原不了 比如Specialities
    tag = pos_tag([word])     # 获取单词词性        
    wordnet_pos = get_wordnet_pos_normalize(tag[0][1]) or wordnet.NOUN#忘了这个or什么意思了，真的有找不到词性的情况？
    wnl_lemma=wnl.lemmatize(tag[0][0], pos=wordnet_pos) # 词形还原
   
    #spacy标准化（词形还原）
    '''
    import en_core_web_sm
    nlp = en_core_web_sm.load()
    doc = nlp(word)
    spacy_lemma=doc[0].lemma_
    return list(set([wnl_lemma,spacy_lemma]))
       '''
    return wnl_lemma
def get_stemming(word):
    result=[]
    # 基于Porter词干提取算法
    from nltk.stem.porter import PorterStemmer  
    porter_stemmer = PorterStemmer()  
    porter_stem=porter_stemmer.stem(word)
    
    # 基于Lancaster 词干提取算法
    from nltk.stem.lancaster import LancasterStemmer  
    lancaster_stemmer = LancasterStemmer()  
    lancaster_stem=lancaster_stemmer.stem(word)
    
    # 基于Snowball 词干提取算法
    from nltk.stem import SnowballStemmer  
    snowball_stemmer = SnowballStemmer('english')  
    snowball_stem=snowball_stemmer.stem(word)
    
    result=list(set([porter_stem,lancaster_stem,snowball_stem]))
    return result

def get_wordnet_pos_normalize(tag):
    '''获取单词的词性，传入wordnet的POS后的标签tag，只是一个映射函数，不是传入词或句子！'''
    if tag.startswith('J'):
        return wordnet.ADJ
    elif tag.startswith('V'):
        return wordnet.VERB
    elif tag.startswith('N'):
        return wordnet.NOUN
    elif tag.startswith('R'):
        return wordnet.ADV
    else:
        return None
    

def get_nltk_pos_single_word(word):
    '''获取用于词形还原的词性，已转换'''
    return get_wordnet_pos_normalize(nltk.pos_tag(nltk.word_tokenize(word))[0][1])
    