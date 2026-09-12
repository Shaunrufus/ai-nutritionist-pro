from setuptools import setup, find_packages

setup(
    name="ai-nutritionist",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'joblib>=1.3.0',
        'scikit-learn>=1.3.0',
        'pandas>=2.0.0',
        'groq>=0.3.0'
    ],
)