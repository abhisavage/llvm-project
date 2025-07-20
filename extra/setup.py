from setuptools import setup, find_packages

setup(
    name='omp_impact2',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'torch',
        'transformers',
        'clang',
        'python-dotenv',
        'unidiff',
        'PyGithub',
        'tqdm',
        'scikit-learn',
    ],
    entry_points={
        'console_scripts': [
            'omp_impact2=omp_impact_recommender.cli_tool:main',
            'feature_impact=omp_impact_recommender.cli_tool:main',
        ],
    },
    include_package_data=True,
)