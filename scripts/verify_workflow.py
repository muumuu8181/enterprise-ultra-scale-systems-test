import os
import django
import sys
from datetime import date

# Add project root to sys.path
sys.path.append(os.getcwd())

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'defense_lms.settings')
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from core.models import User
from logistics.models import Aircraft, Unit
from logistics.views import AircraftViewSet
from maintenance.models import MaintenanceRecord
from maintenance.views import MaintenanceRecordViewSet
from maintenance.serializers import MaintenanceRecordSerializer

def run():
    print("Starting verification workflow...")

    # Create Users
    admin_user, _ = User.objects.get_or_create(username='general', defaults={'clearance_level': 'TOP_SECRET', 'email': 'general@defense.gov'})
    if _:
        admin_user.set_password('password')
        admin_user.save()

    low_user, _ = User.objects.get_or_create(username='recruit', defaults={'clearance_level': 'CONFIDENTIAL', 'email': 'recruit@defense.gov'})
    if _:
        low_user.set_password('password')
        low_user.save()

    print(f"Users created: {admin_user.username} ({admin_user.clearance_level}), {low_user.username} ({low_user.clearance_level})")

    # Create Unit
    unit, _ = Unit.objects.get_or_create(name='301st Tactical Fighter Squadron', defaults={'base_location': 'Misawa Air Base'})

    # Create Aircraft (High Clearance Asset)
    f35, created = Aircraft.objects.get_or_create(
        serial_number='89-8706',
        defaults={
            'name': 'F-35A Lightning II',
            'status': 'OPERATIONAL',
            'acquisition_date': date(2023, 4, 1),
            'required_clearance': 'TOP_SECRET',
            'unit': unit,
            'flight_hours': 150,
            'max_altitude': 50000
        }
    )
    if not created:
        f35.required_clearance = 'TOP_SECRET'
        f35.save()

    # Create Aircraft (Low Clearance Asset) for comparison
    trainer, _ = Aircraft.objects.get_or_create(
        serial_number='12-3456',
        defaults={
            'name': 'T-4 Trainer',
            'status': 'OPERATIONAL',
            'acquisition_date': date(2020, 1, 1),
            'required_clearance': 'CONFIDENTIAL',
            'unit': unit,
            'flight_hours': 500,
            'max_altitude': 30000
        }
    )

    print(f"Assets created: {f35.name} (TOP_SECRET), {trainer.name} (CONFIDENTIAL)")

    factory = APIRequestFactory()
    view_detail = AircraftViewSet.as_view({'get': 'retrieve'})
    view_list = AircraftViewSet.as_view({'get': 'list'})

    # Test 1: Low clearance user accessing Top Secret asset (Detail)
    print("\n[TEST 1] Low clearance user (CONFIDENTIAL) accessing Top Secret asset (Detail)...")
    request = factory.get(f'/api/aircraft/{f35.pk}/')
    force_authenticate(request, user=low_user)
    try:
        response = view_detail(request, pk=f35.pk)
        print(f"Response Status: {response.status_code}")
        if response.status_code == 404:
            print("SUCCESS: Asset not found (Filtered out by QuerySet).")
        elif response.status_code == 403:
             print("SUCCESS: Access Denied.")
        else:
            print(f"FAILURE: Access Granted! Status: {response.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

    # Test 2: Low clearance user listing assets
    print("\n[TEST 2] Low clearance user (CONFIDENTIAL) listing assets...")
    request = factory.get('/api/aircraft/')
    force_authenticate(request, user=low_user)
    response = view_list(request)
    print(f"Response Status: {response.status_code}")
    if response.status_code == 200:
        data = response.data
        if any(item['serial_number'] == '89-8706' for item in data):
            print("FAILURE: Top Secret asset found in list!")
        else:
            print("SUCCESS: Top Secret asset NOT in list.")
            if any(item['serial_number'] == '12-3456' for item in data):
                print("SUCCESS: Confidential asset found in list.")
    else:
        print("FAILURE: List view failed.")

    # Test 3: High clearance user accessing Top Secret asset
    print("\n[TEST 3] High clearance user (TOP_SECRET) accessing Top Secret asset...")
    request = factory.get(f'/api/aircraft/{f35.pk}/')
    force_authenticate(request, user=admin_user)
    response = view_detail(request, pk=f35.pk)
    print(f"Response Status: {response.status_code}")
    if response.status_code == 200:
        print("SUCCESS: Access Granted as expected.")
    else:
        print(f"FAILURE: Access Denied! Status: {response.status_code}")

    # Create Maintenance Record via Serializer (Testing Validation)
    print("\n[TEST 4] Creating Maintenance Record via API (Validation Test)...")

    # 4a: Low clearance user tries to create record for Top Secret asset
    print("  -> Low user trying to create record for F-35 (TOP_SECRET)...")
    data = {
        'equipment': f35.pk,
        'date': str(date.today()),
        'description': 'Attempted unauthorized maintenance.',
        'technician': low_user.pk
    }
    request = factory.post('/api/maintenance-records/', data, format='json')
    force_authenticate(request, user=low_user)
    request.user = low_user # Manually attach user for serializer context since we bypass View processing

    # We use serializer directly to test validation logic used by ViewSet
    serializer = MaintenanceRecordSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        print("FAILURE: Validation passed for unauthorized equipment!")
    else:
        print(f"SUCCESS: Validation failed as expected. Errors: {serializer.errors}")

    # 4b: High clearance user creates record
    print("  -> High user creating record for F-35 (TOP_SECRET)...")
    data['technician'] = admin_user.pk
    data['description'] = 'Authorized maintenance task.'
    request = factory.post('/api/maintenance-records/', data, format='json')
    force_authenticate(request, user=admin_user)
    request.user = admin_user # Manually attach user
    serializer = MaintenanceRecordSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        print("SUCCESS: Validation passed for authorized equipment.")
        record = serializer.save()
        print(f"Maintenance record created: {record}")
    else:
         print(f"FAILURE: Validation failed for authorized user! Errors: {serializer.errors}")

    # Test 5: Verify Maintenance Record Visibility
    print("\n[TEST 5] Low clearance user listing maintenance records...")
    maint_view_list = MaintenanceRecordViewSet.as_view({'get': 'list'})
    request = factory.get('/api/maintenance-records/')
    force_authenticate(request, user=low_user)
    response = maint_view_list(request)

    if response.status_code == 200:
        data = response.data
        # Check if record (if created successfully in 4b) is visible
        # We need the ID from 4b step. But local `record` variable might be undefined if 4b failed.
        # But assume 4b passed.
        try:
             # Find the record created in 4b
             last_record = MaintenanceRecord.objects.last()
             if last_record and last_record.description == 'Attempted unauthorized maintenance.':
                  print("FAILURE: Unauthorized record was created!")
             elif last_record:
                  found = any(item.get('id') == last_record.id for item in data)
                  if found:
                       print("FAILURE: Maintenance record for Top Secret asset visible!")
                  else:
                       print("SUCCESS: Maintenance record correctly hidden.")
        except Exception as e:
             print(f"Error checking record visibility: {e}")

    else:
        print(f"FAILURE: List view failed with status {response.status_code}")

if __name__ == '__main__':
    run()
