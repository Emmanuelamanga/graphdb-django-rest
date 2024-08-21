
from SPARQLWrapper import JSONLD, SPARQLWrapper, JSON
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .models import BlazegraphConnection
from .serializers import BlazegraphConnectionSerializer
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from .models import UploadedFile
from .serializers import UploadedFileSerializer
import os 

@api_view(['POST'])
def import_ttl(request):
    url = request.POST.get('url_endpoint')
    file = request.FILES.get('file')

    if not url or not file:
        return Response({"error": "Url and file are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        sparql_endpoint = url

        
        payload = file.read()
        
        headers = {
            "Content-Type": "application/x-turtle",
        }

        response = requests.post(sparql_endpoint, data=payload, headers=headers)

        if response.status_code == 200:
            return Response({"message": "File imported successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": response.text}, status=response.status_code)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Define where files should be stored
UPLOAD_DIR = "uploaded_files/"

@api_view(['POST'])
def upload_ttl_file(request):
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
        
    if 'files' not in request.FILES:
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

    files = request.FILES.getlist('files')
    uploaded_files = []

    for file in files:
        # if file.content_type not in ['application/x-turtle', 'application/rdf+xml', 'text/csv']:
        #     return Response({"error": f"Unsupported file format: {file.name}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save the file to the server
        file_path = os.path.join(UPLOAD_DIR, file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        uploaded_file = UploadedFile.objects.create(name=file.name, size=file.size, file_path=file_path)
        uploaded_files.append(uploaded_file)
    
    return Response({"message": "File(s) uploaded successfully"}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def list_uploaded_files(request):
    files = UploadedFile.objects.all()
    serializer = UploadedFileSerializer(files, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
def list_blazegraph_namespaces(request):
    url = request.data.get('url')

    if not url:
        return Response({"error": "URL is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Send a GET request to the Blazegraph namespaces page
        response = requests.get(url + "/namespace")

        if response.status_code == 200:
            # Parse the XML response using BeautifulSoup with the XML parser
            soup = BeautifulSoup(response.text, 'xml')  # Set the feature to "xml"
            namespaces = []

            # Find all the namespace entries in the XML
            for namespace in soup.find_all('Namespace'):
                namespace_info = {
                    'name': namespace.get_text(strip=True),
                    'sparqlEndpoint': namespace.find_next('sparqlEndpoint').get('rdf:resource') if namespace.find_next('sparqlEndpoint') else None
                }
                namespaces.append(namespace_info)

            return Response({"namespaces": namespaces}, status=status.HTTP_200_OK)
        else:
            return Response({"error": response.text}, status=response.status_code)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def create_blazegraph_namespace(request):
    url = request.data.get('endpointUrl')
    namespace = request.data.get('namespace')
    timeout = request.data.get('timeout', 0)
    maxResults = request.data.get('maxResults', 1000)
    print(request.data)
    if not url or not namespace:
        return Response({"error": "url and namespace are required"}, status=status.HTTP_400_BAD_REQUEST)

    # Define the URL for creating the namespace
    url = f"{url}/namespace"

    # Define the payload for creating the namespace
    payload = f"""
    com.bigdata.rdf.sail.namespace={namespace}
    com.bigdata.rdf.sail.truthMaintenance=false
    com.bigdata.rdf.store.AbstractTripleStore.textIndex=false
    com.bigdata.rdf.store.AbstractTripleStore.justify=false
    com.bigdata.rdf.store.AbstractTripleStore.statementIdentifiers=false
    com.bigdata.namespace.test.spo.com.bigdata.btree.BTree.branchingFactor=1024
    com.bigdata.rdf.store.AbstractTripleStore.axiomsClass=com.bigdata.rdf.axioms.NoAxioms
    com.bigdata.rdf.store.AbstractTripleStore.quads=false
    com.bigdata.rdf.store.AbstractTripleStore.geoSpatial=false
    com.bigdata.journal.Journal.groupCommit=false
    com.bigdata.rdf.sail.isolatableIndices=false
    com.bigdata.namespace.test.lex.com.bigdata.btree.BTree.branchingFactor=400
    com.bigdata.rdf.sparql.MaxQueryTimeMS={timeout}
    com.bigdata.rdf.sparql.MaxResults={maxResults}
    """

    try:
        # Send the request to create the namespace
        headers = {
            'Content-Type': 'text/plain'
        }
        response = requests.post(url, data=payload, headers=headers)

        # Check if the namespace was successfully created
        if response.status_code == 201:
            return Response({"message": "Namespace created successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": response.text}, status=response.status_code)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def connect_blazegraph(request):
    ip_address = request.data.get('ip_address')
    port = request.data.get('port')
    namespace = request.data.get('database_type', None)
  
    if not ip_address or not port:
        return Response({"error": "IP address and port are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Construct the endpoint URL
        if namespace:
            endpoint_url = f"http://{ip_address}:{port}/{namespace}"
        else:
            endpoint_url = f"http://{ip_address}:{port}"
            
        # Attempt to connect to Blazegraph using SPARQLWrapper
        sparql = SPARQLWrapper(endpoint_url)
        
        # Test the connection by running a simple ASK query
        sparql.setQuery('ASK WHERE { ?s ?p ?o }')
        sparql.setReturnFormat(JSON)
        
        result = sparql.query().convert()
        
        # If the ASK query is successful, proceed to fetch metadata
        if result:
            # Fetch Blazegraph metadata
            # sparql.setQuery("""
            #     SELECT ?metric ?value
            #     WHERE {
            #         SERVICE <http://192.168.100.37:9999/bigdata> {
            #             ?metric ?p ?value .
            #         }
            #     }
            # """)
            # sparql.setReturnFormat(JSONLD)
            # metadata_result = sparql.query().convert()

            # Parse the metadata results, ensuring bytes are converted to JSON
            # metadata = {}
            # for binding in metadata_result['results']['bindings']:
            #     metric = binding['metric']['value']
            #     value = binding['value']['value']
            #     metadata[metric] = value
            
            # Return successful connection message along with metadata
            return Response({
                "message": "Connected to Blazegraph successfully",
                "ip_address": ip_address,
                "port": port,
                "namespace": namespace,
                "endpoint_url": endpoint_url,
                # "metadata": metadata_result
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to connect to Blazegraph"}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_blazegraph_connection(request):
    """
    Test the connection to Blazegraph and store it if successful.
    """
    try:
        name = request.data.get('name')
        endpoint_url = request.data.get('endpoint_url')

        sparql = SPARQLWrapper(endpoint_url)
        sparql.setQuery('ASK WHERE { ?s ?p ?o }')
        sparql.setReturnFormat(JSON)
        
        result = sparql.query().convert()
        
        if result:
            BlazegraphConnection.objects.filter(is_active=True).update(is_active=False)

            new_connection = BlazegraphConnection.objects.create(
                name=name,
                endpoint_url=endpoint_url,
                is_active=True
            )

            serializer = BlazegraphConnectionSerializer(new_connection)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": "Failed to connect to Blazegraph"}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
