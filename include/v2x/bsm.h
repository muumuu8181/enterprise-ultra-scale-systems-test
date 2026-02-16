#ifndef V2X_BSM_H
#define V2X_BSM_H

#include <string>
#include <cstdint>

namespace v2x {

struct BasicSafetyMessage {
    std::string vehicle_id;
    double latitude;
    double longitude;
    double speed_mps;
    double heading_degrees;
    uint64_t timestamp_ms;
};

} // namespace v2x

#endif // V2X_BSM_H
