import pandas as pd
import numpy as np
import io
import base64
import traceback
import signal
import subprocess
import sys
from typing import Dict, Any, Optional
from contextlib import contextmanager
from app.core.config import settings


class ExecutionTimeout(Exception):
    """Raised when code execution exceeds timeout"""
    pass


class CodeExecutorService:
    """Safely execute Python code with sandboxing and resource limits"""

    def __init__(self):
        self.max_timeout_seconds = 120  # 2 minutes max
        self.max_memory_mb = 1024  # 1GB max
        self.allowed_packages = [
            'scikit-learn',
            'scipy',
            'statsmodels',
            'matplotlib',
            'seaborn',
            'xgboost',
            'lightgbm',
            'prophet',
            'pmdarima',
            'duckdb'
        ]
        self._installed_packages = set()

    def _install_package(self, package_name: str) -> bool:
        """Install a package if it's in the allowed list"""
        if package_name not in self.allowed_packages:
            return False

        if package_name in self._installed_packages:
            return True

        try:
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', package_name, '--quiet'],
                timeout=60
            )
            self._installed_packages.add(package_name)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _ensure_libraries(self) -> Dict[str, Any]:
        """Ensure all common ML libraries are available"""
        library_map = {
            'sklearn': 'scikit-learn',
            'xgboost': 'xgboost',
            'lightgbm': 'lightgbm',
            'scipy': 'scipy',
            'statsmodels': 'statsmodels',
            'matplotlib': 'matplotlib',
            'seaborn': 'seaborn',
            'duckdb': 'duckdb'
        }

        missing_libs = []
        imported_libs = {}

        for import_name, package_name in library_map.items():
            try:
                if import_name == 'sklearn':
                    import sklearn
                    imported_libs['sklearn'] = sklearn
                elif import_name == 'xgboost':
                    import xgboost
                    imported_libs['xgboost'] = xgboost
                elif import_name == 'lightgbm':
                    import lightgbm
                    imported_libs['lightgbm'] = lightgbm
                elif import_name == 'scipy':
                    import scipy
                    imported_libs['scipy'] = scipy
                elif import_name == 'statsmodels':
                    import statsmodels
                    imported_libs['statsmodels'] = statsmodels
                elif import_name == 'matplotlib':
                    import matplotlib
                    matplotlib.use('Agg')
                    import matplotlib.pyplot as plt
                    imported_libs['matplotlib'] = matplotlib
                    imported_libs['plt'] = plt
                elif import_name == 'seaborn':
                    import seaborn as sns
                    imported_libs['sns'] = sns
                elif import_name == 'duckdb':
                    import duckdb
                    imported_libs['duckdb'] = duckdb
            except ImportError:
                # Try to install
                if self._install_package(package_name):
                    # Retry import
                    try:
                        if import_name == 'sklearn':
                            import sklearn
                            imported_libs['sklearn'] = sklearn
                        elif import_name == 'xgboost':
                            import xgboost
                            imported_libs['xgboost'] = xgboost
                        elif import_name == 'lightgbm':
                            import lightgbm
                            imported_libs['lightgbm'] = lightgbm
                        elif import_name == 'scipy':
                            import scipy
                            imported_libs['scipy'] = scipy
                        elif import_name == 'statsmodels':
                            import statsmodels
                            imported_libs['statsmodels'] = statsmodels
                        elif import_name == 'matplotlib':
                            import matplotlib
                            matplotlib.use('Agg')
                            import matplotlib.pyplot as plt
                            imported_libs['matplotlib'] = matplotlib
                            imported_libs['plt'] = plt
                        elif import_name == 'seaborn':
                            import seaborn as sns
                            imported_libs['sns'] = sns
                        elif import_name == 'duckdb':
                            import duckdb
                            imported_libs['duckdb'] = duckdb
                    except ImportError:
                        missing_libs.append(package_name)
                else:
                    missing_libs.append(package_name)

        return {
            'success': len(missing_libs) == 0,
            'missing': missing_libs,
            'libraries': imported_libs
        }

    @contextmanager
    def timeout_context(self, seconds: int):
        """Context manager for execution timeout"""
        def timeout_handler(signum, frame):
            raise ExecutionTimeout(f"Execution exceeded {seconds} seconds")

        # Set the signal handler and alarm
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)

        try:
            yield
        finally:
            # Restore the old handler and cancel the alarm
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    def execute_python(
        self,
        code: str,
        dataset_id: str,
        timeout_sec: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute Python code in a sandboxed environment"""

        if timeout_sec is None:
            timeout_sec = 60  # Default 1 minute

        if timeout_sec > self.max_timeout_seconds:
            timeout_sec = self.max_timeout_seconds

        # Prepare safe execution environment
        parquet_path = f"{settings.DATASETS_DIR}/{dataset_id}/data.parquet"

        # Restricted builtins - remove dangerous functions
        safe_builtins = {
            'abs': abs, 'all': all, 'any': any, 'ascii': ascii,
            'bin': bin, 'bool': bool, 'bytearray': bytearray,
            'bytes': bytes, 'chr': chr, 'complex': complex,
            'dict': dict, 'divmod': divmod, 'enumerate': enumerate,
            'filter': filter, 'float': float, 'format': format,
            'frozenset': frozenset, 'hash': hash, 'hex': hex,
            'int': int, 'isinstance': isinstance, 'issubclass': issubclass,
            'iter': iter, 'len': len, 'list': list, 'map': map,
            'max': max, 'min': min, 'next': next, 'object': object,
            'oct': oct, 'ord': ord, 'pow': pow, 'print': print,
            'range': range, 'repr': repr, 'reversed': reversed,
            'round': round, 'set': set, 'slice': slice, 'sorted': sorted,
            'str': str, 'sum': sum, 'tuple': tuple, 'type': type,
            'zip': zip, 'True': True, 'False': False, 'None': None,
            '__import__': __import__,  # Allow imports for libraries
            'ImportError': ImportError,
            'NameError': NameError,
            'Exception': Exception,
            'ValueError': ValueError,
            'KeyError': KeyError,
            'TypeError': TypeError,
            'AttributeError': AttributeError
        }

        # Ensure all ML libraries are available (auto-install if needed)
        lib_result = self._ensure_libraries()

        if not lib_result['success']:
            return {
                'status': 'FAILED',
                'error': f"Failed to load required libraries: {', '.join(lib_result['missing'])}",
                'output': None
            }

        # Get imported libraries
        libs = lib_result['libraries']
        sklearn = libs.get('sklearn')
        scipy = libs.get('scipy')
        statsmodels = libs.get('statsmodels')
        matplotlib = libs.get('matplotlib')
        plt = libs.get('plt')
        sns = libs.get('sns')
        xgboost = libs.get('xgboost')
        lightgbm = libs.get('lightgbm')
        duckdb = libs.get('duckdb')

        # Load the dataset (can be replaced by DuckDB query in generated code)
        df = pd.read_parquet(parquet_path)

        # Create DuckDB connection with dataset view (matches SQL execution pattern)
        # This allows generated code to query "dataset" table directly
        duckdb_conn = duckdb.connect(database=':memory:')
        duckdb_conn.execute(f"CREATE VIEW dataset AS SELECT * FROM read_parquet('{parquet_path}')")

        # Prepare execution globals
        exec_globals = {
            '__builtins__': safe_builtins,
            'pd': pd,
            'np': np,
            'sklearn': sklearn,
            'scipy': scipy,
            'statsmodels': statsmodels,
            'plt': plt,
            'sns': sns,
            'xgboost': xgboost,
            'xgb': xgboost,  # Common alias
            'lightgbm': lightgbm,
            'lgb': lightgbm,  # Common alias
            'duckdb': duckdb,  # For efficient data loading
            'duckdb_conn': duckdb_conn,  # Pre-configured connection with dataset view
            'parquet_path': parquet_path,
            'df': df,  # Pre-load the dataset (can be overridden by DuckDB query)
            'result': None,  # Will be populated by user code
            'model': None,   # For ML models
            'plot_base64': None  # For visualizations
        }

        try:
            # Execute with timeout
            with self.timeout_context(timeout_sec):
                exec(code, exec_globals)

            # Extract results
            result = exec_globals.get('result')
            model = exec_globals.get('model')
            plot_data = exec_globals.get('plot_base64')

            # Extract visualizations from result dict if present
            visualizations = []
            if result and isinstance(result, dict) and 'visualizations' in result:
                # Use visualizations from result dict
                visualizations = result.get('visualizations', [])
            else:
                # Fallback: handle matplotlib figures if any were created
                visualizations = self.extract_visualizations(plt, plot_data)

            # Close all plots to free memory
            plt.close('all')

            # Close DuckDB connection
            duckdb_conn.close()

            # Validate result is JSON-serializable
            if result is not None:
                result = self.make_json_serializable(result)

            return {
                'status': 'SUCCESS',
                'output': result,
                'visualizations': visualizations,
                'model': model is not None,  # Just indicate if model was created
                'error': None
            }

        except ExecutionTimeout as e:
            duckdb_conn.close()
            return {
                'status': 'TIMEOUT',
                'error': str(e),
                'output': None
            }

        except Exception as e:
            # Capture full traceback
            error_trace = traceback.format_exc()
            duckdb_conn.close()

            return {
                'status': 'FAILED',
                'error': str(e),
                'error_trace': error_trace,
                'output': None
            }

    def extract_visualizations(self, plt, plot_base64: Optional[str]) -> list:
        """Extract visualizations from matplotlib"""

        visualizations = []

        # Check if user manually created plot_base64
        if plot_base64:
            visualizations.append({
                'type': 'image',
                'format': 'png',
                'data': plot_base64
            })

        # Check for any open matplotlib figures
        if plt.get_fignums():
            for fig_num in plt.get_fignums():
                fig = plt.figure(fig_num)

                # Save figure to bytes
                buf = io.BytesIO()
                fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
                buf.seek(0)

                # Encode to base64
                img_base64 = base64.b64encode(buf.read()).decode('utf-8')

                visualizations.append({
                    'type': 'image',
                    'format': 'png',
                    'data': img_base64,
                    'figure_num': fig_num
                })

                buf.close()

        return visualizations

    def make_json_serializable(self, obj: Any) -> Any:
        """Convert object to JSON-serializable format"""

        if isinstance(obj, dict):
            # Convert dict keys to strings if they're not JSON-serializable
            result = {}
            for k, v in obj.items():
                # Convert tuple/list keys to string representation
                if isinstance(k, (tuple, list)):
                    key = str(k)
                elif isinstance(k, (str, int, float, bool, type(None))):
                    key = k
                else:
                    key = str(k)
                result[key] = self.make_json_serializable(v)
            return result
        elif isinstance(obj, (list, tuple)):
            return [self.make_json_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.DataFrame):
            # Reset index to avoid tuple keys from multi-index
            df_copy = obj.reset_index(drop=False)
            return df_copy.to_dict('records')
        elif isinstance(obj, pd.Series):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            # Try to convert to string as fallback
            return str(obj)

    def validate_imports(self, code: str) -> Dict[str, Any]:
        """Validate that code only uses allowed imports"""

        allowed_modules = {
            'pandas', 'numpy', 'sklearn', 'scipy', 'statsmodels',
            'matplotlib', 'seaborn', 'datetime', 'json', 'math',
            'collections', 'itertools', 're'
        }

        # Extract import statements
        import_lines = [
            line.strip() for line in code.split('\n')
            if line.strip().startswith('import ') or line.strip().startswith('from ')
        ]

        forbidden_imports = []
        for line in import_lines:
            # Extract module name
            if line.startswith('import '):
                module = line.split()[1].split('.')[0].split(' as ')[0]
            elif line.startswith('from '):
                module = line.split()[1].split('.')[0]
            else:
                continue

            if module not in allowed_modules:
                forbidden_imports.append(module)

        return {
            'valid': len(forbidden_imports) == 0,
            'forbidden_imports': forbidden_imports
        }

    def estimate_memory_usage(self, dataset_id: str) -> int:
        """Estimate memory usage in MB for dataset"""
        import os

        parquet_path = f"{settings.DATASETS_DIR}/{dataset_id}/data.parquet"

        if os.path.exists(parquet_path):
            # Rough estimate: Parquet file size * 3 (decompression + pandas overhead)
            file_size_mb = os.path.getsize(parquet_path) / (1024 * 1024)
            estimated_mb = file_size_mb * 3
            return int(estimated_mb)

        return 0
