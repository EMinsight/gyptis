#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# This file is part of gyptis
# Version: 1.1.2
# License: MIT
# See the documentation at gyptis.gitlab.io

"""
pkg_resources compatibility shim for Python 3.12+

This module provides a minimal pkg_resources API for legacy packages
that haven't migrated to importlib.metadata yet.

Copyright (c) 2024
License: MIT or BSD (choose based on your gyptis license)
"""
import sys
from importlib.metadata import version, PackageNotFoundError, distributions
import warnings


class Distribution:
    """Minimal Distribution class to mimic pkg_resources.Distribution"""
    
    def __init__(self, name):
        self.project_name = name
        self.key = name.lower()
        
        # Try to get version, handling both hyphen and underscore naming
        try:
            self.version = version(name)
        except PackageNotFoundError:
            try:
                self.version = version(name.replace('-', '_'))
            except PackageNotFoundError:
                try:
                    self.version = version(name.replace('_', '-'))
                except PackageNotFoundError:
                    warnings.warn(
                        f"Could not find version for package '{name}'. "
                        "Using '0.0.0' as fallback.",
                        RuntimeWarning
                    )
                    self.version = "0.0.0"


def get_distribution(name):
    """
    Get distribution metadata for a package.
    
    Args:
        name: Package name (e.g., 'fenics-ufl', 'numpy')
    
    Returns:
        Distribution object with .version attribute
    """
    return Distribution(name)


def require(requirements):
    """
    Ensure packages are available (simplified version).
    
    Args:
        requirements: String or list of requirement specifications
    
    Returns:
        List of Distribution objects
    """
    if isinstance(requirements, str):
        requirements = [requirements]
    
    results = []
    for req in requirements:
        # Parse requirement (simplified - just gets package name)
        pkg_name = req.split()[0].split('>=')[0].split('==')[0].split('<')[0]
        results.append(get_distribution(pkg_name))
    
    return results


def working_set():
    """
    Get all installed distributions (simplified version).
    
    Returns:
        List of Distribution objects for all installed packages
    """
    return [Distribution(dist.name) for dist in distributions()]


# Inject this module as pkg_resources into sys.modules
sys.modules['pkg_resources'] = sys.modules[__name__]