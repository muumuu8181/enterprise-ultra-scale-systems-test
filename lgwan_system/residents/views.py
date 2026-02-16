from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Household, Resident
from common.models import AuditLog
import json
import hashlib
from functools import wraps

def require_auth(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Simple token auth for prototype
        auth_header = request.headers.get('Authorization')
        if auth_header != 'Bearer secret-token-123':
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(require_auth, name='dispatch')
class MoveInView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            address = data.get('address')
            residents_data = data.get('residents', [])

            if not address or not residents_data:
                return JsonResponse({'error': 'Missing address or residents data'}, status=400)

            household = Household.objects.create(address=address)

            created_residents = []
            for res_data in residents_data:
                raw_my_number = res_data.get('my_number')
                hashed_my_number = hashlib.sha256(raw_my_number.encode()).hexdigest()

                resident = Resident.objects.create(
                    household=household,
                    name_kanji=res_data.get('name_kanji'),
                    name_kana=res_data.get('name_kana'),
                    dob=res_data.get('dob'),
                    gender=res_data.get('gender'),
                    my_number=hashed_my_number,
                    status='ACTIVE'
                )
                created_residents.append({
                    'id': resident.id,
                    'name': resident.name_kanji
                })

            # Audit Log
            AuditLog.objects.create(
                action='CREATE',
                target_model='Household',
                target_object_id=str(household.id),
                details=f"Created household with {len(created_residents)} residents."
            )

            return JsonResponse({
                'message': 'Move-in registered successfully',
                'household_id': household.id,
                'residents': created_residents
            }, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(require_auth, name='dispatch')
class MoveOutView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            resident_id = data.get('resident_id')
            move_out_date = data.get('move_out_date', timezone.now().date())

            resident = get_object_or_404(Resident, id=resident_id)
            resident.status = 'MOVED_OUT'
            resident.move_out_date = move_out_date
            resident.save()

            # Audit Log
            AuditLog.objects.create(
                action='UPDATE',
                target_model='Resident',
                target_object_id=str(resident.id),
                details=f"Resident moved out on {move_out_date}."
            )

            return JsonResponse({
                'message': 'Move-out registered successfully',
                'resident_id': resident.id,
                'status': resident.status
            })

        except Resident.DoesNotExist:
            return JsonResponse({'error': 'Resident not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(require_auth, name='dispatch')
class CertificateView(View):
    def get(self, request, resident_id):
        try:
            resident = get_object_or_404(Resident, id=resident_id)

            # Audit Log
            AuditLog.objects.create(
                action='READ',
                target_model='Resident',
                target_object_id=str(resident.id),
                details=f"Certificate issued for resident {resident.name_kanji}."
            )

            data = {
                'certificate_type': 'Juminhyo',
                'resident': {
                    'name_kanji': resident.name_kanji,
                    'name_kana': resident.name_kana,
                    'dob': resident.dob,
                    'address': resident.household.address,
                    'gender': resident.gender,
                    'status': resident.status,
                    'issued_at': timezone.now()
                }
            }
            return JsonResponse(data)
        except Resident.DoesNotExist:
            return JsonResponse({'error': 'Resident not found'}, status=404)
