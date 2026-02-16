#ifndef V2X_COMM_MANAGER_H
#define V2X_COMM_MANAGER_H

#include "v2x/bsm.h"
#include <vector>

namespace v2x {

class CommunicationManager {
public:
    CommunicationManager();
    ~CommunicationManager();

    void send_bsm(const BasicSafetyMessage& bsm);
    std::vector<BasicSafetyMessage> receive_bsms();

private:
    std::vector<BasicSafetyMessage> message_buffer_;
};

} // namespace v2x

#endif // V2X_COMM_MANAGER_H
