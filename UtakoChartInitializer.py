# coding: utf-8
import codecs
import json

learnFile = codecs.open("dat/chartlist.json",'r','utf-8')
learn_data = json.load(learnFile,encoding = 'utf-8')
learnFile.close()

res = []

for mov in learn_data.values():
    status = False
    if len(mov) == 25:
        for i,cell in enumerate(mov):
            if i != 24:
                if cell[0] < i*60 or (cell[0] > (i+1)*60):
                    break
            elif 10140 < cell[0] and cell[0] < 10200:
                status = True
        if status:
            res.append(mov)
print(len(res))

initfile = codecs.open("dat/chartlist_init.json",'w','utf-8')
json.dump(res,initfile,ensure_ascii = False)
initfile.close()

if __name__ == '__main__':
    pass
