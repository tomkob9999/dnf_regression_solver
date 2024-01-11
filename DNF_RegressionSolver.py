# Name: DNF_Regression_solver
# Author: tomio kobayashi
# Version: 2.1.11
# Date: 2024/01/11

import itertools
from sympy.logic import boolalg
import numpy as np

import sklearn.datasets
import pandas as pd
import random

class DNF_Regression_solver:
# This version has no good matches
# Instead, all true matches are first added, and some are removed when 
# false unmatch exists and there is no corresponding other rule
    def __init__(self):
        self.expression = ""
        
    def convTuple2bin(t, width):
        i = 1
        ret = 0
        for x in t:
            ii = i << width - x - 1
            ret = ret | ii
        return ret

    #     This needs to be separate function because the condition 
    #     variables cannot have conflict with function variables.  Thus "__XXX__" format is used to prevent naming conflicts.    
#     def myeval(__ccc___, __tokens___, __inp___):
    def myeval(self, __ccc___, __tokens___):
        for __jjjj___ in range(len(__tokens___)):
            exec(__tokens___[__jjjj___] + " = " + str(__ccc___[__jjjj___]))
        return eval(self.expression)
            
    def solve(self, inp, check_negative=True):
        numvars = len(inp[0])
        
        if check_negative:
            for i in range(numvars):
                inp[0].insert(i+numvars, "n_" + inp[0][i])
            for j in range(1, len(inp), 1):
                for i in range(numvars):
                    inp[j].insert(i+numvars,"0" if inp[j][i] == "1" else "1")
            numvars *= 2
        
        tokens = [inp[0][i] for i in range(len(inp[0])-1)]
#         inp_list = np.array([np.array([inp[i][j] for j in range(len(inp[i]))]) for i in range(1, len(inp), 1)])
        inp_list = [[inp[i][j] for j in range(len(inp[i]))] for i in range(1, len(inp), 1)]
        res = list(range(len(inp_list)))
        for i in range(len(inp_list)):
            res[i] = self.myeval(inp_list[i], tokens)

        return res

    def generate_segment_ranks(df, num_segments, name):
    #     df = pd.DataFrame({name: data})
    #     print("df", df)
        df[name + '_rank'] = pd.cut(df[name], bins=num_segments, labels=False)
        df[name + '_label'] = pd.cut(df[name], bins=num_segments, labels=[f'{name} {i+1}' for i in range(num_segments)])
        return df

    def discretize_data(headers, values, byFour=1):

    #     lst = [['apple', 'red', 11], ['grape', 'green', 22], ['orange', 'orange', 33], ['mango', 'yellow', 44]] 
    #     data = pd.DataFrame(values, columns =headers, dtype = float) 
        data = pd.DataFrame(values, columns=headers) 

        cols = [c for c in data.columns]
        for c in cols:
            countNonBool = len(data[c]) - (data[c] == 0).sum() - (data[c] == 1).sum()
            if countNonBool > 0 and pd.api.types.is_numeric_dtype(data[c]):
                result_df = DNF_Regression_solver.generate_segment_ranks(data, byFour*4, c)
                one_hot_df = pd.get_dummies(result_df[c + '_rank'], prefix=c)
                one_hot_df = one_hot_df.astype(int)
                data = pd.concat([result_df, one_hot_df], axis=1)

        # data = data.filter(lambda col: (col == 0).all() or (col == 1).all())
        # data = data.loc[:, (data == 0) | (data == 1).any()]

        cols = [c for c in data.columns]
        new_cols = []
        for c in cols:
            countNonBool = len(data[c]) - (data[c] == 0).sum() - (data[c] == 1).sum()
            if countNonBool == 0 and pd.api.types.is_numeric_dtype(data[c]):
                new_cols.append(c)

        # print(new_cols)
        data = data.filter(items=new_cols)

        data_list = [data.columns.tolist()] + data.values.tolist()
        return data_list
        
    def train(self, file_path=None, data_list=None, max_dnf_len=6, check_negative=True, check_false=True, error_tolerance=0.02):

# file_path: input file in tab-delimited text
# check_negative: enable to check the negative conditions or not.  This one is very heavy.
# max_dnf_len: max length of AND clauses in output DNF.  
#       Increasing this one is heavey especially if check_negative is True
# drop_fake: enable to drop the clause that met the true condition, but not false condition.  This one is heavy.

        # Example usage:
        # file_path = '/kaggle/input/dnf-regression/dnf_regression.txt'
        # file_path = '/kaggle/input/tomio5/dnf_regression.txt'

        inp = None
        if file_path is not None:
            with open(file_path, 'r') as f:
                inp = [line.strip().split('\t') for line in f]
        else:
            inp = data_list

        numvars = len(inp[1])-1

        if check_negative:
            for i in range(numvars):
                inp[0].insert(i+numvars, "n_" + inp[0][i])
            for j in range(1, len(inp), 1):
                for i in range(numvars):
                    inp[j].insert(i+numvars,"0" if inp[j][i] == "1" else "1")
            numvars *= 2

        if max_dnf_len > numvars - 1:
            max_dnf_len = numvars - 1
            
        dic = dict()
        
        true_list = []
        false_list = []
        for i in range(1, len(inp), 1):
            s = ""
            for j in range(len(inp[i]) - 1):
#                 s += inp[i][j]
                s += str(inp[i][j])
            truefalse = inp[i][len(inp[i]) - 1]
            dic[int(s, 2)] = truefalse
            if truefalse == '1':
                true_list.append(s)
            else:
                false_list.append(s)

        dnf_perf = list()
        raw_perf = list()
        raw_perf2 = list()
        for s in range(max_dnf_len):
            len_dnf = s + 1
            l = [ii for ii in range(numvars)]
            p_list = list(itertools.combinations(l, len_dnf))

            true_test_pass = True
            for i in range(len(p_list)):
                match_and_break = False
                b = DNF_Regression_solver.convTuple2bin(p_list[i], numvars)
                for p in raw_perf2:
                    if p == b & p:
                        match_and_break = True
                        break
                if match_and_break:
                    continue
                r = [v for k,v in dic.items() if k & b == b]
                if len(r) == 0:
                    continue
#                 if len([f for f in r if f == "0"]) > 0:
                cnt_all = len([f for f in r])
                cnt_unmatch = len([f for f in r if f == "0"])
                if cnt_unmatch/cnt_all > error_tolerance:
                    continue

                raw_perf.append([ii for ii in p_list[i]])
                raw_perf2.append(b)
        
        for dn in raw_perf:
            dnf_perf.append([inp[0][ii] for ii in dn])

            
        dnf_perf_n = list()
        raw_perf_n = list()
        raw_perf2_n = list()
        if check_false:
            for s in range(max_dnf_len):
                len_dnf = s + 1
                l = [ii for ii in range(numvars)]
                p_list = list(itertools.combinations(l, len_dnf))

                true_test_pass = True
                for i in range(len(p_list)):
                    match_and_break = False
                    b = DNF_Regression_solver.convTuple2bin(p_list[i], numvars)
                    for p in raw_perf2_n:
                        if p == b & p:
                            match_and_break = True
                            break
                    if match_and_break:
                        continue
                    r = [v for k,v in dic.items() if k & b == b]
                    if len(r) == 0:
                        continue
#                     if len([f for f in r if f == "1"]) > 0:
                    cnt_all = len([f for f in r])
                    cnt_unmatch = len([f for f in r if f == "1"])
                    if cnt_unmatch/cnt_all > error_tolerance:
                        continue

                    raw_perf_n.append([ii for ii in p_list[i]])
                    raw_perf2_n.append(b)
        
        for dn in raw_perf_n:
            dnf_perf_n.append([inp[0][ii] for ii in dn])

        set_dnf_true = set(["(" + s + ")" for s in [" & ".join(a) for a in dnf_perf]])
        dnf_common = None
        set_dnf_false = None
        if check_false:
            set_dnf_false = set([word.strip() for word in str(boolalg.to_dnf("(" + ") & (".join([" | ".join(a) for a in [[a[2:] if a[0:2] == "n_" else "n_" + a for a in aa] for aa in dnf_perf_n]]) + ")")).split("|")])

            if len(set_dnf_false) == 1 and list(set_dnf_false)[0] != "(":
                set_dnf_false = set(["(" + list(set_dnf_false)[0] + ")"])
            dnf_common = set_dnf_true & set_dnf_false
        else:
            dnf_common = set_dnf_true
            
        self.expression = " | ".join(dnf_common) if check_false else " | ".join(set_dnf_true)
#         print("set_dnf_true", set_dnf_true)
#         print("set_dnf_false", set_dnf_false)
            
        if check_false:
            print("")
            print("DNF COMMON - " + str(len(dnf_common)))
            print("--------------------------------")

            if len(dnf_common) > 0:
                print(" | ".join(dnf_common))
            
        print("")
        print("DNF TRUE - " + str(len(set_dnf_true)))
        print("--------------------------------")

        if len(set_dnf_true) > 0:
            print(" | ".join(set_dnf_true))

        if check_false:
            print("")
            print("DNF FALSE - " + str(len(set_dnf_false)))
            print("--------------------------------")
            if len(set_dnf_false) > 0:
                print(" | ".join(set_dnf_false))
            
        perm_vars = list(set([xx for x in dnf_perf for xx in x] + [xx for x in dnf_perf_n for xx in x]))
        not_picked = [inp[0][ii] for ii in range(len(inp[0])-1) if inp[0][ii] not in perm_vars]

        print("")
#         print("Unsolved variables - " + str(len(not_picked)) + "/" + str(len(perm_vars)))
        print("Unsolved variables - " + str(len(not_picked)) + "/" + str(len(inp[0])-1))
        print("--------------------------------")
        print(not_picked)


file_path = '/kaggle/input/tomio2/dnf_regression.txt'

reg = DNF_Regression_solver()
reg.train(file_path, error_tolerance=0.03)


with open(file_path, 'r') as f:
    inp = [line.strip().split('\t') for line in f]

answer = [int(inp[i][-1]) for i in range(1, len(inp), 1)]
print("answer", answer)

inp = [[inp[i][j] for j in range(len(inp[i])-1)] for i in range(len(inp))]

  
# print(inp)
res = reg.solve(inp)
print("res", res)

