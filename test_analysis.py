import unittest
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from analyze import COLUMNS, analyze, export

class CreditTests(unittest.TestCase):
    def setUp(self):
        self.data=pd.DataFrame({c:[1.,2.,3.,4.] for c in COLUMNS})
    def test_pairwise_missingness(self):
        self.data.loc[0,'loan_int_rate']=np.nan
        summary,corr,pairs,audit=analyze(self.data)
        self.assertEqual(summary.loc['loan_int_rate','missing_percent'],25)
        self.assertEqual(pairs.loc['loan_int_rate','person_income'],3)
        self.assertAlmostEqual(corr.loc['loan_int_rate','person_income'],1)
        self.assertEqual(audit['rows_complete_on_numeric_columns'],3)
    def test_insufficient_and_constant_pairs(self):
        self.data['person_age']=1
        self.data.loc[:1,'loan_int_rate']=np.nan
        _,corr,_,_=analyze(self.data)
        self.assertTrue(np.isnan(corr.loc['person_age','person_income']))
        self.assertTrue(np.isnan(corr.loc['loan_int_rate','person_income']))
    def test_audit_retains_duplicates_and_flags(self):
        self.data.loc[0,'person_age']=120
        self.data.loc[1,'person_emp_length']=50
        self.data.loc[2,'loan_amnt']=-1
        data=pd.concat([self.data,self.data.iloc[[3]]],ignore_index=True)
        audit=analyze(data)[3]
        self.assertEqual(audit['rows'],5)
        self.assertEqual(audit['exact_duplicate_rows'],1)
        self.assertEqual(audit['age_above_100'],1)
        self.assertEqual(audit['employment_years_above_age'],1)
        self.assertEqual(audit['negative_value_counts']['loan_amnt'],1)
    def test_reject_invalid(self):
        for data in [self.data.iloc[:0],self.data.drop(columns='loan_amnt'),self.data.assign(loan_amnt=np.inf),self.data.assign(person_age='invalid')]:
            with self.assertRaises(ValueError):analyze(data)
    def test_export(self):
        with tempfile.TemporaryDirectory() as folder:
            export(self.data,folder)
            self.assertEqual(len(list(Path(folder).iterdir())),5)
            self.assertIn('<svg',(Path(folder)/'missingness.svg').read_text())

if __name__=='__main__':unittest.main()
