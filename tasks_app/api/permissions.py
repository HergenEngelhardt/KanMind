from rest_framework.permissions import BasePermission
from tasks_app.models import Task
from kanban_app.models import Column


class IsTaskBoardMember(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST':
            column_id = request.data.get('column')
            if not column_id:
                return False
            
            try:
                column = Column.objects.get(id=column_id)
                return request.user == column.board.owner or request.user in column.board.members.all()
            except Column.DoesNotExist:
                return False
        
        return True  

    def has_object_permission(self, request, view, obj):
        return request.user == obj.column.board.owner or request.user in obj.column.board.members.all()


class IsTaskAssigneeOrBoardOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (obj.assignee == request.user or 
                request.user == obj.column.board.owner)


class IsCommentAuthorOrBoardOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user or request.user == obj.task.column.board.owner


class IsTaskReviewer(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user in obj.reviewers.all()