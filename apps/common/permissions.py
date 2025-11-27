"""
Custom permission classes for SmartHR
"""

from rest_framework import permissions


class IsEmployer(permissions.BasePermission):
    """
    Permission to check if user is an employer
    """
    
    message = "You must be an employer to perform this action."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'employer'
        )


class IsCandidate(permissions.BasePermission):
    """
    Permission to check if user is a candidate
    """
    
    message = "You must be a candidate to perform this action."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'candidate'
        )


class IsGovernment(permissions.BasePermission):
    """
    Permission to check if user is a government official
    """
    
    message = "You must be a government official to access this resource."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'gov'
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.user == request.user


class IsEmployerOfJob(permissions.BasePermission):
    """
    Permission to check if user is the employer who posted the job
    """
    
    message = "You must be the employer who posted this job."
    
    def has_object_permission(self, request, view, obj):
        # For Job objects
        if hasattr(obj, 'employer'):
            return obj.employer == request.user
        
        # For Application objects
        if hasattr(obj, 'job'):
            return obj.job.employer == request.user
        
        return False


class IsApplicationOwner(permissions.BasePermission):
    """
    Permission for application owner or job employer
    """
    
    def has_object_permission(self, request, view, obj):
        # Candidate can access their own application
        if obj.user == request.user:
            return True
        
        # Employer can access applications to their jobs
        if request.user.is_employer and obj.job.employer == request.user:
            return True
        
        return False