import numpy as np
from src.constants.limits import MAX_GROUP_SIZE,MIN_GROUP_SIZE
def chord_matrix(a,b):
    angles=np.deg2rad(np.r_[a,b]);xy=np.column_stack([np.cos(angles),np.sin(angles)])
    return np.sqrt(np.maximum(0,((xy[:,None]-xy[None,:])**2).sum(axis=2)))
def statistic(distance,left,right):
    n=len(left);m=len(right)
    return max(0.0,float(2*distance[np.ix_(left,right)].sum()/(n*m)-distance[np.ix_(left,left)].sum()/n**2-distance[np.ix_(right,right)].sum()/m**2))
# 排序后弦距精确恒等式：θj≥θi时 d(i,j)=2|sin((θi-θj)/2)|=2[sin(θj/2)cos(θi/2)-cos(θj/2)sin(θi/2)]，
# 组内/交叉距离和由半角正余弦的前缀和O(N)求得；不抽样、不分箱、不近似距离。
def _within_pairs(cos_h,sin_h,labels):
    c=np.where(labels,cos_h,0.0);s=np.where(labels,sin_h,0.0)
    cp=np.cumsum(c)-c;sp=np.cumsum(s)-s
    return float(2*np.sum(labels*(sin_h*cp-cos_h*sp)))
def _energy(cos_h,sin_h,total,labels,n,m):
    wa=_within_pairs(cos_h,sin_h,labels);wb=_within_pairs(cos_h,sin_h,~labels);cross=total-wa-wb
    return max(0.0,2.0*cross/(n*m)-2.0*wa/n**2-2.0*wb/m**2)
def compare(a,b,repetitions,seed):
    a=np.asarray(a,float);b=np.asarray(b,float)
    if min(len(a),len(b))<MIN_GROUP_SIZE or max(len(a),len(b))>MAX_GROUP_SIZE:raise ValueError(f'每组须有{MIN_GROUP_SIZE}–{MAX_GROUP_SIZE}个观测')
    if not np.isfinite(a).all() or not np.isfinite(b).all() or ((np.r_[a,b]<0)|(np.r_[a,b]>=360)).any():raise ValueError('角度须在[0,360)')
    if not 1<=repetitions<=999:raise ValueError('置换次数无效')
    n=len(a);m=len(b);order=np.arange(n+m)
    pooled=np.r_[a,b];sort_order=np.argsort(pooled,kind='stable');half=np.deg2rad(pooled[sort_order])*0.5
    cos_h=np.cos(half);sin_h=np.sin(half);total=_within_pairs(cos_h,sin_h,np.ones(n+m,dtype=bool))
    labels=np.zeros(n+m,dtype=bool);labels[:n]=True
    observed=_energy(cos_h,sin_h,total,labels[sort_order],n,m);rng=np.random.default_rng(seed);null=[]
    for _ in range(repetitions):
        perm=rng.permutation(order);labels.fill(False);labels[perm[:n]]=True
        null.append(_energy(cos_h,sin_h,total,labels[sort_order],n,m))
    extreme=sum(x>=observed-1e-12 for x in null)
    return {'statistic':observed,'p_value':(extreme+1)/(repetitions+1),'extreme':extreme,'permutations':repetitions,'seed':seed,'null_statistics':null,'null_quantiles':np.quantile(null,[.025,.5,.975]).tolist(),'definition':'V-energy: 2 mean cross chord distance - mean within A (diagonal included) - mean within B; upper-tail label permutation with +1 correction'}
