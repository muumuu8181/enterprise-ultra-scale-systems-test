#include "v2x/comm_manager.h"
#include <iostream>

namespace v2x {

CommunicationManager::CommunicationManager() {
    // Initialize communication resources
}

CommunicationManager::~CommunicationManager() {
    // Clean up resources
}

void CommunicationManager::send_bsm(const BasicSafetyMessage& bsm) {
    std::cout << "[V2X] Sending BSM: ID=" << bsm.vehicle_id
              << " Lat=" << bsm.latitude
              << " Lon=" << bsm.longitude
              << " Speed=" << bsm.speed_mps << "m/s" << std::endl;

    // Simulate network loopback for testing
    message_buffer_.push_back(bsm);
}

std::vector<BasicSafetyMessage> CommunicationManager::receive_bsms() {
    std::vector<BasicSafetyMessage> received = message_buffer_;
    message_buffer_.clear();
    return received;
}

} // namespace v2x
