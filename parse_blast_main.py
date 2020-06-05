import pandas as pd
import re
import os
import sys
import argparse

parser = argparse.ArgumentParser()

#MAIN ARGS
parser.add_argument("blast_file", type=str,
                    help="blast file format outfmt 6")

#OPTION
parser.add_argument("-t", "--name_file_te", type=str, default=None,
                    help="file TE for get size")
parser.add_argument("-p", "--min_pident", type=int, default=94,
                    help="minimum percend of identity [94]")
parser.add_argument("-s", "--min_size_percent", type=int, default=90,
                    help="minimum precent size of TE [90]")
parser.add_argument("-r", "--min_read_support", type=int, default=1,
                    help="minimum read support number [1]")

args = parser.parse_args()

#name_file_TE = "TE_Dm_LTR.fa"
#name_file    = "./BLAST/G73vsG73LR_cnTE.bln"

name_file = args.blast_file

min_pident       = args.min_pident
min_size_percent = args.min_size_percent
min_read_support = args.min_read_support


size_et = {}

if args.name_file_te != None:
    #GET_SIZE CANNONICAL TE
    file  = open(args.name_file_te, "r")
    lines = file.readlines()

    for i, l in enumerate(lines):
        if l[0] == ">":
            size_et[l[1:].strip()] = len(lines[i + 1].strip())
else :
    size_et = {'Idefix': 7411, '17.6': 7439, '1731': 4648, '297': 6995, '3S18': 6126, '412': 7567, 'aurora-element': 4263, 'Burdock': 6411, 'copia': 5143, 'gypsy': 7469, 'mdg1': 7480, 'mdg3': 5519, 'micropia': 5461, 'springer': 7546, 'Tirant': 8526, 'flea': 5034, 'opus': 7521, 'roo': 9092, 'blood': 7410, 'ZAM': 8435, 'GATE': 8507, 'Transpac': 5249, 'Circe': 7450, 'Quasimodo': 7387, 'HMS-Beagle': 7062, 'diver': 6112, 'Tabor': 7345, 'Stalker': 7256, 'gtwin': 7411, 'gypsy2': 6841, 'accord': 7404, 'gypsy3': 6973, 'invader1': 4032, 'invader2': 5124, 'invader3': 5484, 'gypsy4': 6852, 'invader4': 3105, 'gypsy5': 7369, 'gypsy6': 7826, 'invader5': 4038, 'diver2': 4917, 'Dm88': 4558, 'frogger': 2483, 'rover': 7318, 'Tom1': 410, 'rooA': 7621, 'accord2': 7650, 'McClintock': 6450, 'Stalker4': 7359, 'Stalker2': 7672, 'Max-element': 8556, 'gypsy7': 5486, 'gypsy8': 4955, 'gypsy9': 5349, 'gypsy10': 6006, 'gypsy11': 4428, 'gypsy12': 10218, 'invader6': 4885, 'Helena': 1317, 'HMS-Beagle2': 7220, 'Osvaldo': 1543}
    print("SIZE TE DEFAULT", list(size_et.keys())[:5], "...")

#GET BLAST OUTFMT -
df = pd.read_csv(name_file, "\t", header=None)

name_file_withou_ext = name_file.split("/")[-1].split(".")[0] + "_"
print(name_file_withou_ext)

name_genome = name_file_withou_ext.split("vs")[0]
os.system("mkdir -p "+name_genome)

df.columns = ["qseqid", "sseqid", "pident", "length", "mismatch", "gapopen", "qstart", "qend", "sstart", "send", "evalue", "bitscore"]

#KEEP ONLY LTR cf. (GET_SIZE CANNONICAL TE)
df = df[df["sseqid"].isin(size_et.keys())]

#CALCUL SIZE AND PERCENT SIZE
tab_percent = []
tab_size    = []
for index, row in enumerate(df[["sseqid", "qend", "qstart"]].values):
    size_element = abs(int(row[1])-int(row[2]))#qend - qstart
    tab_percent.append(round((size_element/size_et[row[0]]) * 100, 1))
    tab_size.append(size_element)
    


df["size_per"] = tab_percent
df["size_el"]  = tab_size
df = df[df["size_per"] >= min_size_percent]
df = df[df["pident"] >= min_pident]
df = df.sort_values(by=["sseqid"])
df = df[["sseqid", "qseqid", "pident", "size_per", "size_el", "mismatch", "gapopen", "qstart", "qend", "sstart", "send", "evalue", "bitscore"]]

#display(df.head())
print(df.shape)

#GET BEST SCORE
best_score_match = []
best_score_match_index = []
chaine = ""
for index, row in enumerate(df.values):
    
    chaine = df["qseqid"].values[index] + df["sseqid"].values[index]
    if chaine not in best_score_match:
        qseqid       = df["qseqid"].values[index]
        info_qseqid  = qseqid.split(":")
        read_support = int(info_qseqid[5])

        df_tmp        = df[df["qseqid"] == qseqid]
        maxe_bitscore = max(df_tmp["bitscore"].values)
        df_best_score = df_tmp[df_tmp["bitscore"] == maxe_bitscore]
        
        chaine = df_best_score["qseqid"].values[0] + df_best_score["sseqid"].values[0]
        best_score_match.append(chaine)
        
        #Insert only
        find_INS = re.search("INS", df_best_score["qseqid"].values[0])
        if find_INS and read_support >= min_read_support:
            best_score_match_index.append(index)
    
    
df = df.iloc[best_score_match_index]

#display(df.head())
print(df.shape)

#SECOND CRITERE (FACULTATIF)
tab_i = []
for i, v in enumerate(df.values):
    qseqid  = df["qseqid"].values[i]
    qsstart = int(qseqid.split(":")[2])
    qsstop  = int(qseqid.split(":")[3])
    qssize  = int(abs(qsstop-qsstart))
    sseqid  = df["sseqid"].values[i]
    if qssize <= size_et[sseqid] + 18:##########################################
        tab_i.append(i)

        
df = df.iloc[tab_i]
print(df.shape)
df.to_csv(name_genome + "/" + name_file_withou_ext + "ALL_ET.csv", sep="\t", index=None)
