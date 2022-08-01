import pandas as pd
import torch
from torch.utils.data import Dataset
import numpy as np
import glob

CLASSLIST = {0: 'BENIGN', 1: 'Infiltration', 2: 'Bot', 3: 'PortScan', 4: 'DDoS', 5: 'FTP-Patator', 6: 'SSH-Patator', 7: 'DoS slowloris', 8: 'DoS Slowhttptest', 9: 'DoS Hulk', 10: 'DoS GoldenEye', 11: 'Heartbleed', 12: 'Web Attack � Brute Force', 13: 'Web Attack � XSS', 14:'Web Attack � Sql Injection'}

#note, this is a very modified version of a dataloader found in https://www.youtube.com/watch?v=ZoZHd0Zm3RY
class NetworkDataset(Dataset):
    def __init__(self,csv_files=glob.glob("datasets/*.csv"),transforms=None, benign=None, ignore=None):
        self.transforms = transforms
        self.isOneHot = True
        self.lengths = []
        self.list = []
        classlist = []
        for x,_ in enumerate(csv_files):
            csv = pd.read_csv(csv_files[x],header=0)
            #count the unique number of classes, even if you are dropping things
            classlist.append(csv[" Label"].unique())

            #If I understand correctly this should allow you to sort just benign or malicious packets 
            #https://stackoverflow.com/questions/18172851/deleting-dataframe-row-in-pandas-based-on-column-value
            if benign == True:
                csv = csv[csv[" Label"]=="BENIGN"]
            else:
                if benign == False:
                    csv = csv[csv[" Label"]!="BENIGN"]

            if ignore is not None:
                for i in ignore:
                    csv = csv[csv[" Label"]!=i]

            csv.replace(np.inf, np.nan, inplace=True)
            csv.replace(-np.inf, np.nan, inplace=True)
            csv.fillna(-1,inplace=True)
            #csv.dropna(inplace=True)

            csv.reset_index(drop=True,inplace=True)
            self.list.append(csv)
            self.lengths.append(len(csv))
            #
            # 
            
            




        #find how many classes are in the data 
        classlist = np.concatenate(classlist)
        self.classes = pd.DataFrame(classlist)[0].unique()
        classes = {}
        classes = {b:a for a,b in enumerate(self.classes)}
        self.classes = classes


    def __len__(self):
        total = 0
        for length in self.lengths:
            total += length
        return total

    def __getitem__(self, index):
        currentlist = 0
        while index >= self.lengths[currentlist]:
            index = index-self.lengths[currentlist]
            currentlist += 1

        currentlist = self.list[currentlist]
        
        data = currentlist.iloc[[index]].to_numpy()
        data = data[0][:len(data[0])-1]
        data = torch.tensor(data.astype(np.float))

        label = currentlist[" Label"][index]
        label = self.classes[label]
        label = torch.tensor(label)

        #add transformations if they exist
        if(self.transforms):
            data = self.transforms(data)
            #image = image/255.0

        #output labels are in single hot encoded vectors
        if self.isOneHot:
            return data, np.eye(len(self.classes))[label]
        else:
            return data, label


def leftOutMask(classes:int,batchsize, itemLeftOut:int):
    if classes<itemLeftOut:
        return torch.zeros((batchsize,classes))
    fullmask = torch.ones((batchsize,classes))
    fullmask[:,itemLeftOut] = 0
    return fullmask

