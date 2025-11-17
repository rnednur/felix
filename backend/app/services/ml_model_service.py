import pickle
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from app.core.config import settings


class MLModelService:
    """Manage ML model persistence, versioning, and metadata"""

    def __init__(self):
        self.models_dir = Path(settings.DATA_DIR) / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def save_model(
        self,
        model: Any,
        dataset_id: str,
        model_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save ML model to disk with metadata"""

        model_id = str(uuid.uuid4())
        model_path = self.models_dir / f"{model_id}.pkl"
        metadata_path = self.models_dir / f"{model_id}_metadata.json"

        # Serialize model
        try:
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to serialize model: {str(e)}"
            }

        # Prepare metadata
        metadata = {
            'model_id': model_id,
            'dataset_id': dataset_id,
            'model_type': model_metadata.get('model_type', 'unknown'),
            'features': model_metadata.get('features', []),
            'target_column': model_metadata.get('target_column'),
            'metrics': model_metadata.get('metrics', {}),
            'training_info': model_metadata.get('training_info', {}),
            'model_path': str(model_path),
            'created_at': datetime.utcnow().isoformat(),
            'framework': self.detect_framework(model)
        }

        # Save metadata
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        return {
            'success': True,
            'model_id': model_id,
            'model_path': str(model_path),
            'metadata': metadata
        }

    def load_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Load ML model from disk"""

        model_path = self.models_dir / f"{model_id}.pkl"
        metadata_path = self.models_dir / f"{model_id}_metadata.json"

        if not model_path.exists():
            return None

        # Load model
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to load model: {str(e)}"
            }

        # Load metadata
        metadata = {}
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

        return {
            'success': True,
            'model': model,
            'metadata': metadata
        }

    def predict(
        self,
        model_id: str,
        input_data: Any
    ) -> Dict[str, Any]:
        """Make predictions using saved model"""

        # Load model
        loaded = self.load_model(model_id)
        if not loaded or not loaded.get('success'):
            return {
                'success': False,
                'error': 'Model not found or failed to load'
            }

        model = loaded['model']
        metadata = loaded['metadata']

        # Make predictions
        try:
            predictions = model.predict(input_data)

            # Try to get prediction probabilities if classifier
            probabilities = None
            if hasattr(model, 'predict_proba'):
                try:
                    probabilities = model.predict_proba(input_data)
                except:
                    pass

            return {
                'success': True,
                'predictions': predictions.tolist() if hasattr(predictions, 'tolist') else predictions,
                'probabilities': probabilities.tolist() if probabilities is not None else None,
                'model_type': metadata.get('model_type'),
                'features': metadata.get('features')
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Prediction failed: {str(e)}"
            }

    def list_models(self, dataset_id: Optional[str] = None) -> list:
        """List all saved models, optionally filtered by dataset"""

        models = []

        for metadata_file in self.models_dir.glob("*_metadata.json"):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            # Filter by dataset if specified
            if dataset_id and metadata.get('dataset_id') != dataset_id:
                continue

            models.append(metadata)

        # Sort by creation date (newest first)
        models.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return models

    def delete_model(self, model_id: str) -> bool:
        """Delete model and its metadata"""

        model_path = self.models_dir / f"{model_id}.pkl"
        metadata_path = self.models_dir / f"{model_id}_metadata.json"

        deleted = False

        if model_path.exists():
            model_path.unlink()
            deleted = True

        if metadata_path.exists():
            metadata_path.unlink()
            deleted = True

        return deleted

    def detect_framework(self, model: Any) -> str:
        """Detect which ML framework the model is from"""

        model_type = type(model).__module__

        if 'sklearn' in model_type:
            return 'scikit-learn'
        elif 'statsmodels' in model_type:
            return 'statsmodels'
        elif 'xgboost' in model_type:
            return 'xgboost'
        elif 'lightgbm' in model_type:
            return 'lightgbm'
        else:
            return 'unknown'

    def get_model_summary(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive model summary"""

        loaded = self.load_model(model_id)
        if not loaded or not loaded.get('success'):
            return None

        model = loaded['model']
        metadata = loaded['metadata']

        summary = {
            'model_id': model_id,
            'model_type': metadata.get('model_type'),
            'framework': metadata.get('framework'),
            'features': metadata.get('features'),
            'target_column': metadata.get('target_column'),
            'metrics': metadata.get('metrics'),
            'created_at': metadata.get('created_at'),
            'model_params': {}
        }

        # Extract model-specific information
        if hasattr(model, 'get_params'):
            try:
                summary['model_params'] = model.get_params()
            except:
                pass

        # Feature importance for tree-based models
        if hasattr(model, 'feature_importances_'):
            features = metadata.get('features', [])
            importances = model.feature_importances_.tolist()
            summary['feature_importance'] = [
                {'feature': feat, 'importance': imp}
                for feat, imp in zip(features, importances)
            ]
            summary['feature_importance'].sort(key=lambda x: x['importance'], reverse=True)

        # Coefficients for linear models
        if hasattr(model, 'coef_'):
            features = metadata.get('features', [])
            coefficients = model.coef_.tolist() if hasattr(model.coef_, 'tolist') else [model.coef_]
            summary['coefficients'] = [
                {'feature': feat, 'coefficient': coef}
                for feat, coef in zip(features, coefficients)
            ]

        return summary

    def export_model_code(self, model_id: str) -> Optional[str]:
        """Generate Python code to recreate and use the model"""

        loaded = self.load_model(model_id)
        if not loaded or not loaded.get('success'):
            return None

        metadata = loaded['metadata']

        code = f"""# Model: {model_id}
# Type: {metadata.get('model_type')}
# Created: {metadata.get('created_at')}

import pandas as pd
import pickle
from sklearn.model_selection import train_test_split

# Load the saved model
with open('{metadata.get('model_path')}', 'rb') as f:
    model = pickle.load(f)

# Features used for training
features = {metadata.get('features')}
target = '{metadata.get('target_column')}'

# To make predictions on new data:
# 1. Load your data
# df = pd.read_csv('your_data.csv')

# 2. Prepare features (same columns used in training)
# X = df[features]

# 3. Make predictions
# predictions = model.predict(X)

# Model metrics on training data:
# {json.dumps(metadata.get('metrics', {}), indent=2)}
"""

        return code
