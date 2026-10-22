# Contributing

Keep runtime behavior deterministic and local. New validation rules should have a stable issue code, a focused unit test, and a short contract or architecture documentation update when they change the public format.

Before opening a pull request, run `PYTHONPATH=src python -m unittest discover -s tests -v` and `PYTHONPATH=src python -m compileall -q src tests`. Keep commits focused on one behavior change and explain compatibility impact when changing contract semantics.
