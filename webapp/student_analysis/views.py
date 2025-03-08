import json
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
import base64
import os
from django.conf import settings


@ensure_csrf_cookie  # This decorator ensures the CSRF cookie is set
@require_GET
def student_analysis_view(request):
    """Simple view to display student analysis data from a JSON file."""
    try:
        # Load the JSON data
        with open('student_analyses.json', 'r') as f:
            analyses = json.load(f)

        # Pass the data to the template
        return render(request, 'student_analysis.html', {'analyses': analyses})

    except FileNotFoundError:
        return HttpResponse("Analysis file not found. Please run the analyzer first.", status=404)
    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON file format.", status=500)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)


@require_POST
def save_image(request):
    """Save webcam image to the server."""
    try:
        # Get image data from the request
        image_data = request.POST.get('image_data')
        timestamp = request.POST.get('timestamp')

        # Create directory if it doesn't exist
        images_dir = os.path.join(settings.MEDIA_ROOT, 'webcam_images')
        os.makedirs(images_dir, exist_ok=True)

        # Create filename with timestamp
        filename = f"webcam_capture_{timestamp}.png"
        filepath = os.path.join(images_dir, filename)

        # Save the image
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(image_data))

        return JsonResponse({
            'success': True,
            'message': 'Image saved successfully',
            'filename': filename
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error saving image: {str(e)}'
        }, status=500)