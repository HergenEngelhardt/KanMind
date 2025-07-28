from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User

from kanban_app.models import Board, Column
from kanban_app.api.serializers.column_serializers import ColumnSerializer
from kanban_app.api.permissions import IsOwnerOrMember


class ColumnListCreateView(generics.ListCreateAPIView):
    """
    List columns for a board or create a new column.
    
    Provides endpoints to retrieve all columns for a specific board
    and create new columns within that board.
    """
    serializer_class = ColumnSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOrMember]

    def get_queryset(self):
        """
        Get columns for the current board ordered by position.
        
        Returns:
            QuerySet: Filtered columns for the specified board
        """
        board_id = self.kwargs.get("board_id")
        return Column.objects.filter(board_id=board_id).order_by('position')

    def perform_create(self, serializer):
        """
        Create a new column for the specified board.
        
        Args:
            serializer (ColumnSerializer): Validated column data
            
        Raises:
            NotFound: If board doesn't exist
            PermissionDenied: If user lacks permission to add columns
        """
        board_id = self.kwargs.get("board_id")
        board = self._get_board_or_raise(board_id)
        self._check_board_permissions(board)
        serializer.save(board=board)

    def _get_board_or_raise(self, board_id):
        """
        Retrieve board by ID or raise NotFound exception.
        
        Args:
            board_id (int): Board primary key
            
        Returns:
            Board: The requested board instance
            
        Raises:
            NotFound: If board with given ID doesn't exist
        """
        try:
            return Board.objects.get(pk=board_id)
        except Board.DoesNotExist:
            raise NotFound("Board not found")

    def _check_board_permissions(self, board):
        """
        Verify user has permission to modify the board.
        
        Args:
            board (Board): Board instance to check permissions for
            
        Raises:
            PermissionDenied: If user lacks permission to add columns
        """
        permission_check = IsOwnerOrMember()
        has_permission = permission_check.has_object_permission(
            self.request, self, board
        )
        if not has_permission:
            raise PermissionDenied(
                "You don't have permission to add columns to this board"
            )


class ColumnDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a specific column.
    
    Provides endpoints for individual column operations including
    viewing, updating, and deleting columns.
    """
    serializer_class = ColumnSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get all columns queryset.
        
        Returns:
            QuerySet: All column objects
        """
        return Column.objects.all()

    def get_object(self):
        """
        Get column object with permission check.
        
        Returns:
            Column: The requested column instance
            
        Raises:
            PermissionDenied: If user lacks access to the column
        """
        obj = super().get_object()
        self._check_column_permissions(obj)
        return obj

    def _check_column_permissions(self, column):
        """
        Verify user has permission to access the column.
        
        Args:
            column (Column): Column instance to check permissions for
            
        Raises:
            PermissionDenied: If user lacks permission to access column
        """
        board = column.board
        is_owner = board.owner == self.request.user
        is_member = self.request.user in board.members.all()
        
        if not (is_owner or is_member):
            raise PermissionDenied(
                "You don't have permission to access this column"
            )


class EmailCheckView(APIView):
    """
    API view to check if a user exists by email and return user information.
    
    Provides endpoint to validate user existence and retrieve basic user data
    by email address.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Handle GET request to check user existence by email.
        
        Args:
            request: HTTP request object containing email in query parameters
            
        Returns:
            Response: JSON response with user data or error message
            
        Raises:
            400: If email parameter is missing
            404: If user with given email does not exist
        """
        email = request.query_params.get('email')
        
        if not email:
            return self._email_missing_response()
        
        return self._get_user_by_email(email)

    def _email_missing_response(self):
        """
        Generate response for missing email parameter.
        
        Returns:
            Response: HTTP 400 response with error message
        """
        return Response(
            {"error": "Email parameter is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    def _get_user_by_email(self, email):
        """
        Retrieve user by email and return appropriate response.
        
        Args:
            email (str): Email address to search for
            
        Returns:
            Response: User data response or not found error
        """
        try:
            user = User.objects.get(email=email)
            return self._user_found_response(user)
        except User.DoesNotExist:
            return self._user_not_found_response()

    def _user_not_found_response(self):
        """
        Generate response for user not found.
        
        Returns:
            Response: HTTP 404 response with error message
        """
        return Response(
            {"error": "User not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

    def _user_found_response(self, user):
        """
        Generate response with user data when user is found.
        
        Args:
            user (User): Django User model instance
            
        Returns:
            Response: HTTP 200 response with user data dictionary
        """
        fullname = self._generate_fullname(user)
        user_data = self._build_user_data(user, fullname)
        
        return Response(user_data, status=status.HTTP_200_OK)

    def _generate_fullname(self, user):
        """
        Generate display name from user's first and last name or fallback.
        
        Args:
            user (User): Django User model instance
            
        Returns:
            str: Generated fullname or fallback to email/username
        """
        first_name = (user.first_name or "").strip()
        last_name = (user.last_name or "").strip()
        
        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
        elif last_name:
            return last_name
        else:
            return user.email.split('@')[0] if user.email else user.username

    def _build_user_data(self, user, fullname):
        """
        Build user data dictionary for API response.
        
        Args:
            user (User): Django User model instance
            fullname (str): Generated display name
            
        Returns:
            dict: Dictionary containing user information
        """
        return {
            "id": user.id,
            "email": user.email,
            "fullname": fullname,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        }