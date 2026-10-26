"""Explore aggregate numeric patterns and data completeness in credit records."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

COLUMNS = ['person_age','person_income','person_emp_length','loan_amnt',
           'loan_int_rate','loan_percent_income','cb_person_cred_hist_length']

def analyze(frame):
    missing = set(COLUMNS) - set(frame.columns)
    if missing: raise ValueError(f'Missing columns: {sorted(missing)}')
    if frame.empty: raise ValueError('Input must contain rows')
    data = frame[COLUMNS].apply(pd.to_numeric, errors='raise')
    if np.isinf(data.to_numpy()).any(): raise ValueError('Infinite numeric values are not supported')
    available = data.notna().astype('int64')
    counts = available.T @ available
    correlations = data.corr(min_periods=3)
    summary = data.describe().T
    summary['missing'] = data.isna().sum()
    summary['missing_percent'] = data.isna().mean()*100
    audit = {'rows':len(frame), 'numeric_columns':len(COLUMNS),
        'exact_duplicate_rows':int(frame.duplicated().sum()),
        'rows_complete_on_numeric_columns':int(data.notna().all(axis=1).sum()),
        'age_above_100':int((data.person_age>100).sum()),
        'employment_years_above_age':int((data.person_emp_length>data.person_age).sum()),
        'negative_value_counts':{c:int((data[c]<0).sum()) for c in COLUMNS},
        'correlation_method':'Pearson, pairwise complete observations, minimum three pairs',
        'row_policy':'All rows retained; duplicate counts and unusual values reported, not automatically removed.'}
    return summary, correlations, counts, audit

def export(frame, output):
    summary,corr,counts,audit=analyze(frame)
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    for name, table in [('numeric_summary',summary),('correlations',corr),('correlation_pair_counts',counts)]:
        table.to_csv(output/f'{name}.csv',na_rep='NA')
    (output/'audit.json').write_text(json.dumps(audit,indent=2,allow_nan=False)+'\n')
    with plt.rc_context({'svg.fonttype':'none'}):
        fig,ax=plt.subplots(figsize=(9,4.5))
        labels=[c.replace('_',' ') for c in COLUMNS]
        ax.barh(labels,summary.missing_percent,color='#227c9d')
        ax.set(xlabel='Missing values (%)',title='Completeness of numeric credit variables')
        ax.invert_yaxis();ax.set_xlim(0,max(10,float(summary.missing_percent.max())*1.2))
        for i,v in enumerate(summary.missing_percent):ax.text(v+.12,i,f'{v:.2f}%',va='center',fontsize=9)
        fig.tight_layout();fig.savefig(output/'missingness.svg');plt.close(fig)
    return audit

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv',type=Path)
    parser.add_argument('--output',type=Path,default=Path('results'))
    args=parser.parse_args()
    print(json.dumps(export(pd.read_csv(args.csv),args.output),indent=2))
