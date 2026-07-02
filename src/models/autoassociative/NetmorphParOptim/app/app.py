import os
import random
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template
from sklearn.model_selection import train_test_split
from quantile_forest import RandomForestQuantileRegressor
import dice_ml

app = Flask(__name__)

# Cache variables
X_train = None
y_train = None
X_test = None
y_test = None
qrf = None
cols = ['days', 'pyramidal', 'minneuronseparation', 'shape.radius', 'shape.thickness', 'dm.weight']

class ConservativeModel:
    def __init__(self, model, threshold):
        self.model = model
        self.threshold = threshold
    
    def predict(self, instances):
        # We predict the 0.025 quantile (Lower Bound)
        return self.model.predict(instances, quantiles=0.025)

def init_model():
    global X_train, y_train, X_test, y_test, qrf
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)
    
    df1_path = os.path.join(parent_dir, 'Phase1_1500_samples-labeled-RS20240628.xlsx')
    df2_path = os.path.join(parent_dir, 'Phase0_700_samples-labeled-RS20240628.xlsx')
    
    print(f"Loading data from {df1_path} and {df2_path}...")
    df1 = pd.read_excel(df1_path)
    df2 = pd.read_excel(df2_path)
    
    df = pd.concat([df1, df2], keys=['t1', 't2'], axis=0)
    if 'usable_conns1' in df.columns:
        df.drop('usable_conns1', axis=1, inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    df = df[(df['usable_conns2'] <= 2500) & (df['usable_conns2'] >= 200)]
    df.reset_index(drop=True, inplace=True)
    
    X_train, X_test, y_train, y_test = train_test_split(df[cols], df['usable_conns2'], test_size=0.2, random_state=42)
    
    print("Fitting RandomForestQuantileRegressor...")
    qrf = RandomForestQuantileRegressor(
        n_estimators=1000, 
        bootstrap=True, 
        max_samples=None, 
        max_features=4, 
        max_depth=20, 
        min_samples_leaf=2, 
        min_samples_split=5, 
        oob_score=True, 
        default_quantiles=0.025,
        random_state=42
    )
    qrf.fit(X_train, y_train)
    print("Model training completed successfully.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/default_values', methods=['GET'])
def get_default_values():
    if X_test is None:
        init_model()
    
    # Select a random sample from the test set as default query instance
    random_idx = random.randint(0, len(X_test) - 1)
    sample_instance = X_test.iloc[random_idx].to_dict()
    
    # Calculate baseline predictions
    sample_df = pd.DataFrame([sample_instance])[cols]
    pred_median = float(qrf.predict(sample_df, quantiles=0.5)[0])
    pred_lower = float(qrf.predict(sample_df, quantiles=0.025)[0])
    
    response = {
        'query_instance': sample_instance,
        'prediction': {
            'median': pred_median,
            'lower': pred_lower
        },
        'permitted_ranges': {
            'days': [20, 25],
            'pyramidal': [16, 128],
            'minneuronseparation': [10, 15],
            'shape.radius': [100, 200],
            'shape.thickness': [20.0, 50.0],
            'dm.weight': [0.3, 0.7]
        },
        'desired_range': [500.0, 2500.0],
        'threshold': 500,
        'features_to_vary': cols
    }
    return jsonify(response)

@app.route('/api/generate', methods=['POST'])
def generate():
    if X_train is None:
        init_model()
        
    data = request.json
    query_instance = data.get('query_instance')
    total_CFs = int(data.get('total_CFs', 7))
    desired_range = data.get('desired_range', [500.0, 2500.0])
    threshold = float(data.get('threshold', 500.0))
    permitted_range = data.get('permitted_range')
    features_to_vary = data.get('features_to_vary', cols)
    
    # Preprocess permitted ranges to ensure lists are floats/ints
    processed_permitted = {}
    for k, v in permitted_range.items():
        processed_permitted[k] = [float(v[0]), float(v[1])]
    
    query_df = pd.DataFrame([query_instance])[cols]
    
    # Run DiCE
    conservative_model = ConservativeModel(qrf, threshold=threshold)
    dice_model = dice_ml.Model(model=conservative_model, backend="sklearn", model_type="regressor")

    dice_data = dice_ml.Data(
        dataframe=pd.concat(
            [X_train[cols].reset_index(drop=True), y_train.reset_index(drop=True)],
            axis=1,
        ),
        continuous_features=cols,
        outcome_name="usable_conns2",
    )

    exp = dice_ml.Dice(dice_data, dice_model, method="random")

    try:
        dice_exp = exp.generate_counterfactuals(
            query_df,
            total_CFs=total_CFs,
            desired_range=desired_range,
            permitted_range=processed_permitted,
            features_to_vary=features_to_vary,
        )
        cf_df = dice_exp.cf_examples_list[0].final_cfs_df.copy()
        
        # Calculate model predicted median and lower bounds for the generated counterfactuals
        cf_records = []
        for idx, row in cf_df.iterrows():
            row_dict = row.to_dict()
            cf_row_df = pd.DataFrame([row_dict])[cols]
            row_dict['pred_median'] = float(qrf.predict(cf_row_df, quantiles=0.5)[0])
            row_dict['pred_lower'] = float(qrf.predict(cf_row_df, quantiles=0.025)[0])
            cf_records.append(row_dict)
            
        # Get query instance prediction
        query_pred_median = float(qrf.predict(query_df, quantiles=0.5)[0])
        query_pred_lower = float(qrf.predict(query_df, quantiles=0.025)[0])
        
        return jsonify({
            'success': True,
            'query_predictions': {
                'median': query_pred_median,
                'lower': query_pred_lower
            },
            'counterfactuals': cf_records
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Initialize the model on startup so first request is fast
    init_model()
    app.run(host='0.0.0.0', port=5001, debug=True)
