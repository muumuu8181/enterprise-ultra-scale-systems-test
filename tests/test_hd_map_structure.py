import sys
import os
import unittest
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.getcwd())

class TestHDMapStructure(unittest.TestCase):

    def test_models_exist(self):
        from src.models.map_models import MapTile, RoadCondition
        # Verify attributes exist on the class (Mapped columns are descriptors)
        self.assertTrue(hasattr(MapTile, 'z'))
        self.assertTrue(hasattr(MapTile, 'data'))
        self.assertTrue(hasattr(RoadCondition, 'condition_type'))

    def test_service_exists(self):
        from src.services.map_updater import MapUpdaterService
        service = MapUpdaterService()
        self.assertTrue(hasattr(service, 'fetch_tile'))
        self.assertTrue(hasattr(service, 'invalidate_cache'))
        self.assertTrue(hasattr(service, 'broadcast_map_update'))
        self.assertTrue(hasattr(service, 'update_map_section'))
        self.assertTrue(hasattr(service, 'report_incident'))

    def test_api_exists(self):
        from src.api.v1.hd_map import router, MapUpdate, IncidentReport, RoadConditionResponse
        # Check router endpoints
        routes = [route.path for route in router.routes]
        print(f"Found routes: {routes}")
        self.assertIn("/map/tiles/{z}/{x}/{y}", routes)
        self.assertIn("/map/updates", routes)
        self.assertIn("/map/road_conditions", routes)
        self.assertIn("/map/incidents/report", routes)

        # Check Pydantic models
        if hasattr(MapUpdate, 'model_fields'):
             self.assertIn('section_id', MapUpdate.model_fields)
             self.assertIn('location', IncidentReport.model_fields)
             self.assertIn('location', RoadConditionResponse.model_fields)
        else:
             # Fallback for V1
             self.assertIn('section_id', MapUpdate.__fields__)
             self.assertIn('location', IncidentReport.__fields__)
             self.assertIn('location', RoadConditionResponse.__fields__)

if __name__ == '__main__':
    unittest.main()
