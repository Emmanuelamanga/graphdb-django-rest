from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import create_blazegraph_connection
from .views import connect_blazegraph
from .views import create_blazegraph_namespace
from .views import list_blazegraph_namespaces
from .views import upload_ttl_file, list_uploaded_files, import_ttl

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('connect-blazegraph/', connect_blazegraph, name='connect_blazegraph'),
    path('create-connection/', create_blazegraph_connection, name='create_connection'),
    path('create-namespace/', create_blazegraph_namespace, name='create_namespace'),
    path('list-namespaces/', list_blazegraph_namespaces, name='list_namespaces'),
    path('upload-ttl/', upload_ttl_file, name='upload_ttl_file'),
    path('list-ttl-files/', list_uploaded_files, name='list_uploaded_files'),
    path('import-ttl/', import_ttl, name='import_ttl'),
]
