import os
import Config
import pandas as pd
import torch

from torch.utils.data import DataLoader
import Dataload
import plots

# hyperpath= r"C:\Users\bgaspard\Desktop\OpenSetPerf\src\main\hyperparam\\"
# unknownpath = r"C:\Users\bgaspard\Desktop\OpenSetPerf\src\main\unknown\\"
# modelsavespath = r"C:\Users\bgaspard\Desktop\OpenSetPerf\src\main\Saves\\"

def generateHyperparameters(root_path):
    if os.path.exists(os.path.join(root_path,"Saves","hyperparam","hyperParam.csv")) and os.path.exists(os.path.join(root_path,"src","main","unknown","unknowns.csv")):
        print("Hyperparam.csv and unknown.csv files exist")
    else:
        print("Either hyperparam.csv or unknown.csv does not exist , generating one based on config file settings ....")
        parameters = Config.parameters
        # print(parameters)
        param = pd.DataFrame.from_dict(parameters, orient="columns")
        param.to_csv(os.path.join(root_path,"Saves","hyperparam","hyperParam.csv"))
        unknown_classes = Config.helper_variables["unknowns_clss"]
        param = pd.DataFrame.from_dict(unknown_classes)
        param.to_csv(os.path.join(root_path,"Saves","unknown","unknowns.csv"))
        print("Files created successfully !")



def readCSVs(root_path):
        param = pd.read_csv(os.path.join(root_path,"Saves","hyperparam","hyperParam.csv"))
        batch_size = int(param["batch_size"][0])
        num_workers = int(param["num_workers"][0])
        attemptLoad = int(param["attemptLoad"][0])
        testlen = float(param["testlength"][0])
        num_epochs = int(param["num_epochs"][0])
        lr = float(param["learningRate"][0])
        threshold = float(param["threshold"][0])
        param = pd.read_csv(os.path.join(root_path,"Saves","unknown","unknowns.csv"))
        unknownVals = param["unknowns"].to_list()
        return batch_size,num_workers,attemptLoad,testlen,num_epochs,lr,threshold,unknownVals


def loopOverUnknowns(unknownlist):
    print(torch.__version__)
    knownVals = list(range(15))
    for un in unknownlist:
        knownVals.remove(un)
    return knownVals

# generateHyperparameters(hyperpath,unknownpath)

# def readFromFiles(path):
def checkAttempLoad(root_path):

    _,_,_,_,_,_,_,unknownlist = readCSVs(root_path)
    # get the data and create a test set and train set
    print("Reading datasets to create test and train sets")
    train = Dataload.Dataset(os.path.join(root_path,"datasets","Payload_data_CICIDS2017"), use=loopOverUnknowns(unknownlist))
    train, test = torch.utils.data.random_split(train,[len(train) - int(len(train) * Config.parameters["testlength"][0]),int(len(train) * Config.parameters["testlength"][0])])  # randomly takes 4000 lines to use as a testing dataset
    unknowns = Dataload.Dataset(os.path.join(root_path,"datasets","Payload_data_CICIDS2017"), use=unknownlist, unknownData=True)
    test = torch.utils.data.ConcatDataset([test, unknowns])
    if Config.parameters["attemptLoad"][0] and os.path.exists(os.path.join(root_path,"Saves","Data.pt")):
        train = torch.load(os.path.join(root_path,"Saves","Data.pt"))
        test = torch.load(os.path.join(root_path,"Saves","DataTest.pt"))
        print("Loading from data and test checkpoint ...")

    else:
        #test = unknowns
        torch.save(train,os.path.join(root_path,"Saves","Data.pt"))
        torch.save(test,os.path.join(root_path,"Saves","DataTest.pt"))
        if Config.parameters["attemptLoad"][0]:
            print("No model train and test checkpoint was found, saving datacheckpoints ...")
    return train, test


def deletefile(path):
    if os.path.exists(path):
        os.remove(path)

def refreshFiles(root_path):

    deletefile(os.path.join(root_path,"Saves","hyperparam","hyperParam.csv"))
    deletefile(os.path.join(root_path,"Saves","unknown","unknowns.csv"))
    deletefile(os.path.join(root_path,"Saves","Data.pt"))
    deletefile(os.path.join(root_path,"Saves","DataTest.pt"))
    #os.remove(os.path.join(root_path,"src","main","test"))
    #os.mkdir(os.path.join(root_path,"src","main","test"))

# def savePoint(net:AttackClassification, path:str, epoch=0, phase=None):


def convert_to_1d(y_test, y_pred):
    y_test_final = []
    y_pred_final = []
    for i in range(len(y_test)):
        for j in range(len(y_pred[i])):
            y_test_final.append(y_test[i][j])
            y_pred_final.append(y_pred[i][j])
    return y_test_final, y_pred_final


def write_hist_to_file(lst, num_epochs, type=""):
    for l in lst:
        l["type"] = type
    if os.path.exists(os.path.join("Saves","history.csv")):
        hist = pd.read_csv(os.path.join("Saves","history.csv"), index_col=0)
        hist = pd.concat((hist, pd.DataFrame.from_dict(lst)))
    else:
        hist = pd.DataFrame.from_dict(lst)
    hist.to_csv(os.path.join("Saves","history.csv"))
    with open(os.path.join('Saves',f'history{type}.txt'), 'a') as fp:
        # fp.write(f"history for {num_epochs} \n")
        fp.write("\n")
        for item in lst:
            # write each item on a new line
            fp.write(f"num_epochs {num_epochs} " + str(item) + "\n")
        print('Writing history Done')


def write_scores_to_file(lst, num_epochs, type=""):
    thisRun = pd.DataFrame.from_dict(lst)
    thisRun["type"] = type
    if os.path.exists(os.path.join("Saves","scores.csv")):
        hist = pd.read_csv(os.path.join("Saves","scores.csv"), index_col=0)
        hist.loc[len(hist)] = thisRun.iloc[0]
    else:
        hist = thisRun

    hist.to_csv(os.path.join("Saves","scores.csv"))
    with open(os.path.join('Saves',f'scores{type}.txt'), 'a') as fp:
        fp.write("\n")
        for item in lst:
            # write each item on a new line
            fp.write(f"num_epochs {num_epochs} " + str(item).format(num_epochs) + "\n")
        print('Writing scores Done')


def write_batch_to_file(loss, num, modeltype="", batchtype=""):
    thisRun = pd.DataFrame([[loss.item(), num, modeltype, batchtype]],
                           columns=["Loss", "Batch Number", "Model Type", "Batch Type"])
    # thisRun["Loss"] = loss.detach()
    # thisRun["Batch Number"] = num
    # thisRun["Model Type"] = modeltype
    # thisRun["Batch Type"] = batchtype
    if os.path.exists(os.path.join("Saves","batch.csv")):
        hist = pd.read_csv(os.path.join("Saves","batch.csv"), index_col=0)
        hist.loc[len(hist)] = thisRun.iloc[0]
    else:
        hist = thisRun

    hist.to_csv(os.path.join("Saves","batch.csv"))


def store_values(history: list, Y_predict: list, Y_test: list, num_epochs: int, end_type: str):
    y_test, y_pred = convert_to_1d(Y_test, Y_predict)
    recall = plots.recall_score(y_test, y_pred, average='weighted', zero_division=0)
    precision = plots.precision_score(y_test, y_pred, average='weighted', zero_division=0)
    f1 = 2 * (precision * recall) / (precision + recall)
    # auprc = average_precision_score(y_test, y_pred, average='samples')
    score_list = [recall, precision, f1]
    write_hist_to_file(history, num_epochs, end_type)
    write_scores_to_file(score_list, num_epochs, end_type)

#     if not os.path.exists(path):
#         os.mkdir(path)
#     torch.save(net.state_dict(),path+f"/Epoch{epoch:03d}.pth")
#     if phase is not None:
#         file = open("Saves/phase","w")
#         file.write(str(phase))
#         file.close()

# def loadPoint(net:AttackClassification, path:str):
#     if not os.path.exists(path):
#         os.mkdir(path)
#     i = 999
#     epochFound = 0
#     while i >= 0:
#         if os.path.exists(path+f"/Epoch{i:03d}.pth"):
#             net.load_state_dict(torch.load(path+f"/Epoch{i:03d}.pth"))
#             print(f"Loaded  model /Epoch{i:03d}.pth")
#             epochFound = i
#             i = -1
#         i = i-1
#     if i != -2:
#         print("No model to load found.")
#     elif os.path.exists(modelsavespath+"phase"):
#         file = open(modelsavespath+"phase","r")
#         phase = file.read()
#         file.close()
#         return int(phase),epochFound
#     return -1, -1
#
#
# def attemptedLoadcheck(model):
#     if attemptLoad and os.path.exists(modelsavespath+"phase"):
#         file = open(modelsavespath+"phase","r")
#         try:
#             startphase = int(file.read())
#         except:
#             startphase = 0
#         file.close()
#
#         model = cnn.Conv1DClassifier()
#         # model = nn.DataParallel(model)
#         model.to(device)
#         _,e = loadPoint(model, modelsavespath+"Saves")
#         e = e
#     for x in ["Soft","Energy","Open"]:
#         phase += 1
#         if phase<startphase:
#             continue
#         elif e==0:
#             model = Net()
#             model.to(device)
#         model.end.type=x
#         if x == "Open":
#             model.end.prepWeibull(train_loader,device,model)
#
#         Y_test = []
#         y_pred =[]
#         history_finaltyped = []
#         history_finaltyped += fit(num_epochs-e, lr, model, train_loader, val_loader, opt_func)
#         plots.store_values(history_finaltyped, y_pred, Y_test, num_epochs, x)
#         e=0
#         del model
#     model = Net()
#     model.to(device)
#     if attemptLoad:
#         loadPoint(model,modelsavespath+"Saves")
#     phase += 1
#
# def phasecheck(modelsavespath)
#     if attemptLoad and os.path.exists(modelsavespath+"phase"):
#         file = open(modelsavespath+"phase","w")
#         startphase = "0"
#         file.close()