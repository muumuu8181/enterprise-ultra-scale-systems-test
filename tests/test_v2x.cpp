#include "v2x/comm_manager.h"
#include <iostream>
#include <cassert>

int main() {
    v2x::CommunicationManager manager;

    v2x::BasicSafetyMessage bsm;
    bsm.vehicle_id = "V001";
    bsm.latitude = 35.6895;
    bsm.longitude = 139.6917;
    bsm.speed_mps = 15.0;
    bsm.heading_degrees = 90.0;
    bsm.timestamp_ms = 1000;

    manager.send_bsm(bsm);

    auto messages = manager.receive_bsms();

    assert(messages.size() == 1);
    assert(messages[0].vehicle_id == "V001");
    assert(messages[0].speed_mps == 15.0);

    std::cout << "Test Passed: BSM sent and received successfully." << std::endl;

    return 0;
}
