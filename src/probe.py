"""Post hoc fixed-hyperparameter supervised linear readout; no hyperparameter search."""
import json
from pathlib import Path
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from analyze import ci
root=Path('results/mechanism');X=np.load(root/'teacher_states.npz')['states'];dirs=np.load(root/'directions.npz');out=[]
labels=np.tile(np.repeat(np.arange(4),4),12)
for li,layer in enumerate([12,24,36,48]):
    train=X[:12,1:,li].reshape(-1,3840);test=X[12:,1:,li].reshape(-1,3840)
    scaler=StandardScaler().fit(train);clf=LogisticRegression(C=1.,solver='lbfgs',max_iter=3000,random_state=19).fit(scaler.transform(train),labels)
    np.savez_compressed(root/f'supervised_probe_layer{layer}.npz',weight=clf.coef_,intercept=clf.intercept_,mean=scaler.mean_,scale=scaler.scale_)
    interventions={'none':test}
    if layer==24:
        ds=dirs['directions'][labels,li];mu=dirs['reference'][li];a=((test-mu)*ds).sum(-1,keepdims=True);interventions['target_projection']=test-a*ds
    for name,data in interventions.items():
        pred=clf.predict(scaler.transform(data));ok=(pred==labels).reshape(12,4,4)
        for pi,pos in enumerate([64,192,384,576]):
            vals=ok[:,:,pi].mean(1);out.append(dict(layer=layer,position=pos,intervention=name,accuracy=float(vals.mean()),ci=ci(vals),train_accuracy=float(clf.score(scaler.transform(train),labels)),n_contexts=12))
    print(layer,'test',float((clf.predict(scaler.transform(test))==labels).mean()),flush=True)
(root/'supervised_probe.json').write_text(json.dumps(out,indent=2))
equal=[]
y=np.tile(np.repeat(np.arange(3),4),12)
for li,layer in enumerate([12,24,36,48]):
    train=X[:12,1:4,li].reshape(-1,3840);test=X[12:,1:4,li].reshape(-1,3840)
    scaler=StandardScaler().fit(train);clf=LogisticRegression(C=1.,solver='lbfgs',max_iter=3000,random_state=19).fit(scaler.transform(train),y)
    ok=(clf.predict(scaler.transform(test))==y).reshape(12,3,4)
    for pi,p in enumerate([64,192,384,576]):
        a=ok[:,:,pi].mean(1);equal.append(dict(layer=layer,position=p,accuracy=float(a.mean()),ci=ci(a),chance=1/3))
(root/'supervised_equal_length.json').write_text(json.dumps(equal,indent=2))
