# -*- coding: utf-8 -*-
"""Final_Churn_modeling.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1xb8bY4121s18Fyu4V50DoednYU3FFiCS
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

import pylab
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from scipy.stats import norm
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.datasets import load_breast_cancer
from sklearn.svm import SVC
from sklearn.linear_model import ElasticNetCV
from sklearn.linear_model import SGDRegressor
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import plot_confusion_matrix, confusion_matrix, classification_report
from sklearn import metrics
from sklearn.svm import SVC

!pip install shap
import shap

!pip install hypertools
import hypertools as hyp

"""**EDA АНАЛИЗ**"""

df = pd.read_excel('WA_Fn-UseC_-HR-Employee-Attrition.xlsx')
df.head(5)

df.describe()

"""Посмотрим на распределения по каждому числовому признаку"""

df.hist(figsize=(20,20))
plt.show()

"""#### Выводы:
* Распределение "Age" можно представить как нормальное распределение. Правда оно немного искажено как вправо, так и влево. 
* EmployeeCount и StandardHours являются избыточными столбцами, так как для всех сотрудников значения одинаковые.
* Многие столбцы смещены и вправо, и влево. Следовательно, понадобится нормализация данных.

### Коррреляция
"""

df_transf = df.copy()
df_transf["Attrition"] = df_transf["Attrition"].apply(
    lambda x: 0 if x == 'No' else 1)

df_transf = df_transf.drop(["EmployeeCount", "StandardHours", 
                            "EmployeeNumber", "Over18"], axis=1)

correlations = df_transf.corr()["Attrition"].sort_values()
print('Most Positive Correlations: \n', correlations.tail(5))
print('\nMost Negative Correlations: \n', correlations.head(5))

corilation_matrix = df_transf.corr()
mask = np.zeros_like(corilation_matrix)
mask[np.triu_indices_from(mask)] = True

# Heatmap
plt.figure(figsize=(15, 10))
sns.heatmap(corilation_matrix, vmax=.5,
            annot=True, fmt=".2f",
            linewidths=.2, cmap="YlGnBu")

"""Из корреляционной матрицы можно заметить:

* Признаки "MonthlyRate", "NumCompaniesWorked" и "DistanceFromHome" положительно коррелируют с выбытием;
* Признаки "Age", "TotalWorkingYears", "MonthlyIncome", "JobLevel" и "YearsInCurrentRole" отрицательно коррелируют с выбытием.

### Посмотрим на выбросы
"""

hyp.plot(df.drop('Attrition', 1), normalize='across', reduce='PCA', ndims=2, fmt='o')

"""Можно заметить, что значения в признаках довольно размашистые. Поэтому, для улучшения качества работы модели, нужно будет провести шкалирование данных

### Заострим внимание на ключевых признаках
"""

attrited_df = df[df["Attrition"] == "Yes"]
attrited_df.head()

"""### 1) Gender"""

# Gender of employees
df['Gender'].value_counts()

sns.set_style('whitegrid')
sns.countplot(x='Gender',data=attrited_df,palette='colorblind')

plt.show()

"""Большинство ушедших - мужской пол

### 2) Education

Посмотрим на процентное соотношение выпускников для каждой области образования
"""

df['EducationField'].value_counts()

import cufflinks as cf
cf.go_offline()
cf.set_config_file(offline=False, world_readable=True)

df_EducationField = pd.DataFrame(columns=["Field", "% of Leavers"])
i=0
for field in list(df['EducationField'].unique()):
    ratio = df[(df['EducationField']==field)&(df['Attrition']=="Yes")].shape[0] / df[df['EducationField']==field].shape[0]
    df_EducationField.loc[i] = (field, ratio*100)
    i += 1
    #print("In {}, the ratio of leavers is {:.2f}%".format(field, ratio*100))    
df_EF = df_EducationField.groupby(by="Field").sum()
df_EF.iplot(kind='bar',title='Leavers by Education Field (%)')

"""Большинство уволившихся имели высокий уровень образования

### 3) Department
"""

df['Department'].value_counts()

sns.set_style('whitegrid')
sns.countplot(x='Department',data=attrited_df,palette='colorblind')

plt.show()

"""Большинство людей уходило из research & Development Department

### 4) Age
"""

(mu, sigma) = norm.fit(df.loc[df['Attrition'] == 'Yes', 'Age'])
print(
    'Ex-exmployees: average age = {:.1f} years old and standard deviation = {:.1f}'.format(mu, sigma))
(mu, sigma) = norm.fit(df.loc[df['Attrition'] == 'No', 'Age'])
print('Current exmployees: average age = {:.1f} years old and standard deviation = {:.1f}'.format(
    mu, sigma))

"""Давайте создадим график оценки плотности ядра (KDE), окрашенный значением целевого объекта. Оценка плотности ядра (KDE) - это непараметрический способ оценки функции плотности вероятности случайной величины. Это позволит нам определить, существует ли корреляция между возрастом Клиента и его способностью вернуть долг."""

plt.figure(figsize=(15,6))
plt.style.use('seaborn-colorblind')
plt.grid(True, alpha=0.5)
sns.kdeplot(df.loc[df['Attrition'] == 'No', 'Age'], label = 'Active Employee')
sns.kdeplot(df.loc[df['Attrition'] == 'Yes', 'Age'], label = 'Ex-Employees')
plt.xlim(left=18, right=60)
plt.xlabel('Age (years)')
plt.ylabel('Density')
plt.title('Age Distribution in Percent by Attrition Status');

sns.set_style('darkgrid')
plt.figure(figsize=(10,10),dpi=80)
sns.countplot(x='Age',data=attrited_df,palette='colorblind')

plt.xlabel('Age')
plt.show()

"""Больше всего людей уходило в возрасте от 26 до 35(достаточно молодые специалисты)

### 5) JobRole
"""

# Employees in the database have several roles on-file
df['JobRole'].value_counts()

sns.set_style('darkgrid')
plt.figure(figsize=(10,10),dpi=80)
sns.countplot(x='JobRole',data=attrited_df,palette='colorblind')

plt.xlabel('JobRole')
plt.xticks(rotation=45)
plt.show()

"""Большинство уволившихся были или техническими лаборантами,или директорами по продажам, или научными исследователями

### 6) DistanceFromHome
"""

print('Average distance from home for currently active employees: {:.2f} miles and ex-employees: {:.2f} miles'.format(
    df[df['Attrition'] == 'No']['DistanceFromHome'].mean(), df[df['Attrition'] == 'Yes']['DistanceFromHome'].mean()))

plt.figure(figsize=(15,6))
plt.style.use('seaborn-colorblind')
plt.grid(True, alpha=0.5)
sns.kdeplot(df.loc[df['Attrition'] == 'No', 'DistanceFromHome'], label = 'Active Employee')
sns.kdeplot(df.loc[df['Attrition'] == 'Yes', 'DistanceFromHome'], label = 'Ex-Employees')
plt.xlabel('DistanceFromHome')
plt.xlim(left=0)
plt.ylabel('Density')
plt.title('Distance From Home Distribution in Percent by Attrition Status')

sns.set_style('darkgrid')
plt.figure(figsize=(10,10),dpi=80)
sns.countplot(x='DistanceFromHome',data=attrited_df,palette='colorblind')

plt.show()

"""Большая часть уволившихся жила рядом с работой

### 7) MaritalStatus
"""

# Marital Status of employees
df['MaritalStatus'].value_counts()

sns.set_style('whitegrid')
sns.countplot(x='MaritalStatus',data=attrited_df,palette='colorblind')

plt.show()

"""большая часть увольвшихся была не жената/не замужем

### 8) RelationshipSatisfaction
"""

sns.set_style('whitegrid')
sns.countplot(x='RelationshipSatisfaction',data=attrited_df,palette='colorblind')

plt.show()

"""Много людей не было удовлетворены коллективом

### 9) EnvironmentSatisfaction
"""

sns.set_style('whitegrid')
sns.countplot(x='EnvironmentSatisfaction',data=attrited_df,palette='colorblind')

plt.show()

"""Большинству не нравилась обстановка на работе

### 10) WorkLifeBalance
"""

sns.set_style('whitegrid')
sns.countplot(x='WorkLifeBalance',data=attrited_df,palette='colorblind')

plt.show()

"""Большинство имело хороший баланс между личной жизнью и работой

### 11) YearsAtCompany
"""

sns.set_style('darkgrid')
plt.figure(figsize=(10,10),dpi=80)
sns.countplot(x='YearsAtCompany',data=attrited_df,palette='colorblind')

plt.show()

"""Большинство не проводило и двух лет в компании """

sns.set_style('darkgrid')
plt.figure(figsize=(10,10),dpi=80)
sns.countplot(x='YearsWithCurrManager',data=attrited_df,palette='colorblind')

plt.show()

"""Большинство и года не пробыло с текущим менеджером"""

sns.set_style('whitegrid')
sns.countplot(x='PerformanceRating',data=attrited_df,palette='colorblind')

plt.show()

"""Все уволившиеся отлично справлялись с работой

"""

for line in df['MonthlyIncome']:
  
    if line >= 2000 and line < 3000:
      attrited_df.loc[(df.MonthlyIncome == line), 'MonthlyIncome' ] = 2500
    elif line >= 3000 and line < 4000:
      attrited_df.loc[(df.MonthlyIncome == line), 'MonthlyIncome' ] = 3500
    elif line >= 4000 and line < 5000:
      attrited_df.loc[(df.MonthlyIncome == line), 'MonthlyIncome' ] = 4500
    elif line >= 5000 and line < 6000:
      attrited_df.loc[(df.MonthlyIncome == line), 'MonthlyIncome' ] = 5500
    elif line >= 6000 and line < 7000:
      attrited_df.loc[(df.MonthlyIncome == line), 'MonthlyIncome' ] = 6500
    elif line >= 7000 and line < 8000:
      attrited_df.loc[(df.MonthlyIncome == line), 'MonthlyIncome' ] = 7500
    elif line >= 8000 and line < 9000:
      attrited_df.loc[(df.MonthlyIncome == line), 'MonthlyIncome' ] = 8500
    elif line >= 9000 and line < 10000:
      attrited_df.loc[(df.MonthlyIncome == line), 'MonthlyIncome' ] = 9500
    elif line >= 10000:
      attrited_df.loc[(df.MonthlyIncome == line), 'MonthlyIncome' ] = 10000


sns.set_style('darkgrid')
plt.figure(figsize=(10,10),dpi=80)
sns.countplot(x='MonthlyIncome',data=attrited_df,palette='colorblind')
plt.xticks(rotation=45)
plt.show()

"""большая часть зарабатывала от 2000 до 3000

ВЫВОД:

Большинство уволившихся в возрасте от 26 до 35 не проработали больше двух лет в компании, а с текущим менеджером и года. У большинства также наблюдается неприязнь к окружающей рабочей обстановке, а также проблема с взаимоотношениями в коллективе. Также многие уволившиеся были или техническими лаборантами или научными исследователями, т.е. были в одном департаменте исследований и разработки и получали достаточно низкую зарплату от 2000 до 3000. У подавляющего числа уволившихся дистанция от дома до работы маленькая, баланс между жизнью и работой хороший

**                                      ПРЕДПРОЦЕССИНГ                                 **
"""

df = pd.read_excel('WA_Fn-UseC_-HR-Employee-Attrition.xlsx')
df.head()

#Заполнение пропущенных значений
df.fillna(0)
df.shape

#Замена значений в столбце Attririon
df.loc[df.Attrition == 'Yes', 'Attrition'] = 1
df.loc[df.Attrition == 'No', 'Attrition'] = 0
df.head()

#Encoding
la_count = 0
la = preprocessing.LabelEncoder()
for col in df.columns[2:]:
    if df[col].dtype == 'object':
        if len(list(df[col].unique())) <= 2:
            la.fit(df[col])
            df[col] = la.transform(df[col])
            la_count += 1
print('{} columns were label encoded.'.format(la_count))

# convert rest of categorical variable into dummy
df= pd.get_dummies(df, drop_first=True)

df.head()

#Сохранение значений Attrition
att = df.loc[:, 'Attrition_1']
att

#Создание DataFrame без "Attrition"
df_no_att = df
df_no_att.pop('Attrition_1')
df_no_att.head()

#Scaling
scale = preprocessing.MinMaxScaler(feature_range=(0,5))
for col in df_no_att.columns:
  df_no_att[col] = df_no_att[col].astype('float')
  df_no_att[[col]] = scale.fit_transform(df_no_att[[col]])
df_no_att.head()

#Разбивка на test и train выборки
X_train, X_test, y_train, y_test = train_test_split(df_no_att, att, test_size=0.25, random_state=42, stratify=att)



"""**Метод опорных векторов**"""

#Обучение через метод опорных векторов
SVM_classifier = SVC()
param_grid = {"C": [0.01, 0.1, 1, 10, 100, 1000], 
              "gamma": [1, 0.1, 0.01, 0.001, 0.0001],
              "kernel": ['rbf']} 
grid = GridSearchCV(SVM_classifier, param_grid, refit = True, verbose = 3)
grid.fit(X_train, y_train)

#Лучший параметр
best_svm = grid.best_estimator_
print(best_svm)

y_pred_svm = best_svm.predict(X_test)
  
# classification report
print(classification_report(y_test, y_pred_svm))

#Confusion matrix
confusion_matrix(y_test, y_pred_svm)

plot_confusion_matrix(grid, X_test, y_test )

#ROC-кривая
fprs, tprs, thr = metrics.roc_curve(y_test, y_pred_svm)
plt.plot(fprs, tprs, marker='o')
plt.xlabel("FPR")
plt.ylabel("TPR")
plt.title('ROC_curve')

metrics.auc(fprs, tprs)

"""Feature Importance для метода опорных векторов

"""

#Feature Importance с более маленьким срезом данных
model = SVC(kernel='rbf', C=10, gamma=0.001)
X_train_50 = X_train.iloc[:50]
y_train_50 = y_train.iloc[:50]
model.fit(X_train_50, y_train_50)
explainer = shap.KernelExplainer(model.predict, X_train_50, link='identity')
expected_value = explainer.expected_value
if isinstance(expected_value, list):
    expected_value = expected_value[1]
print(f"Explainer expected value: {expected_value}")

sum_plot = explainer.shap_values(X_train_50)
shap.summary_plot(sum_plot, X_train_50)

from sklearn.inspection import permutation_importance
# perform permutation importance
results = permutation_importance(grid, X_test, y_test, scoring='accuracy')
# get importance
importance = results.importances_mean
# summarize feature importance
col = X_test.columns
k = 0
for i, v in enumerate(importance):
    print(col[k], '->', sep='', end=' ')
    print('Score: %.5f' % v)
    k+=1
# plot feature importance
plt.figure(figsize=(10, 10))
plt.xticks(rotation = 90)
plt.bar([x for x in col], importance)
plt.show()

"""**Решающие деревья**"""

#Решающие деревья
dtreeClf = DecisionTreeClassifier()
pipe = Pipeline([("GS_CV_tree", dtreeClf)])
parameters_tree = [{'GS_CV_tree__criterion' : ['entropy'], 
                    'GS_CV_tree__max_depth' : [2, 4, 6, 8, 10], 
                    'GS_CV_tree__splitter': ['best'], 
                    'GS_CV_tree__max_features': ['sqrt'], 
                    'GS_CV_tree__min_samples_leaf': [1], 
                    'GS_CV_tree__min_samples_split':[2]}]
grid_search = GridSearchCV(pipe, param_grid=parameters_tree, cv=5, scoring='f1')
grid_search.fit(X_train, y_train)

#Лучший параметр
best_tree = grid_search.best_estimator_

y_pred_tree = best_tree.predict(X_test)
  
# classification report
print(classification_report(y_test, y_pred_tree))

#Confusion matrix
confusion_matrix(y_test, y_pred_tree)
plot_confusion_matrix(grid_search, X_test, y_test )

#ROC-кривая
fprs, tprs, thr = metrics.roc_curve(y_test, y_pred_tree)
plt.plot(fprs, tprs, marker='o')
plt.xlabel("FPR")
plt.ylabel("TPR")
plt.title('ROC_curve')

metrics.auc(fprs, tprs)

"""**Логическая регрессия**"""

#Обучение модели
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(solver='liblinear', class_weight="balanced", random_state=7)
grid = GridSearchCV(model, return_train_score=True, param_grid={'C': np.arange(1e-03, 2, 0.01)}, scoring='roc_auc', cv=10)
grid.fit(X_train, y_train)

grid.best_params_

#Лучший параметр
best_reg = grid.best_estimator_
best_reg

y_reg = best_reg.predict(X_test)

print(classification_report(y_test,y_reg))

#Confusion матрица
from sklearn.metrics import confusion_matrix
from sklearn.metrics import plot_confusion_matrix

confusion_matrix(y_test, y_reg)
plot_confusion_matrix(grid, X_test, y_test )

#ROC-кривая 
from sklearn.metrics import roc_curve, auc


fprs, tprs, thr = roc_curve(y_test, y_reg)
roc_auc = auc(fprs, tprs)
plt.plot(fprs, tprs, color='darkorange')

plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC')
plt.show()

#Метрика логической регрессии
roc_auc = auc(fprs, tprs)
roc_auc

"""`У логической регрессии Score лучше, метрика выше, TPR лучше на ROC-кривой, поэтому выбираем её`

Feature importance для логической регрессии
"""

#feature importance
from sklearn.inspection import permutation_importance
results = permutation_importance(grid, X_test, y_test, scoring='accuracy')
importance = results.importances_mean
col = X_test.columns
k = 0
for i, v in enumerate(importance):
    print(col[k], '->', sep='', end=' ')
    print('Score: %.5f' % v)
    k+=1
plt.figure(figsize=(30, 20))
plt.xticks(rotation = 60)
plt.bar([x for x in col], importance)

plt.show()

model.fit(X_train, y_train)
explainer = shap.KernelExplainer(model.predict, X_train[:100], link='identity')
sum_plot = explainer.shap_values(X_train)
shap.summary_plot(sum_plot, X_train)

X_train_50 = X_train.iloc[:50]
y_train_50 = y_train.iloc[:50]
model.fit(X_train_50, y_train_50)
explainer = shap.KernelExplainer(model.predict, X_train_50, link='identity')
expected_value = explainer.expected_value
if isinstance(expected_value, list):
    expected_value = expected_value[1]
expected_value

select = range(50)
features = X_test.iloc[select]
shap_values = explainer.shap_values(features)[1] 
features_display = X_test.loc[features.index]

shap.decision_plot(expected_value, shap_values, features_display)

shap.decision_plot(expected_value, shap_values, features_display, link='logit') #with probabilities

"""# Анализ диаграммы Feature Importance
На этой диаграмме ось x обозначает значение shap_value, а ось y содержит features. Каждая точка на графике представляет собой одно shap_value для прогноза и feature. Малиновый цвет означает более высокий показатель feature, а синий - более низкий. На основе этой диаграммы можно получить общее представление о влиянии features на прогноз модели на основе распределения малиновых и синих точек.
Судя по диаграмме, сильнее всего на решение людей уволиться согласно модели влияют: высокие переработки; частые командировки; большое число компаний, в которых работал человек; работа в отделе "Sales Representative", а также низкое вовлечение в рабочий процесс и низкое удовлетворение от работы и обстановки.
"""