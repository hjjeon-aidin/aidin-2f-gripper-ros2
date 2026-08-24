// Aidin Gripper SDK - public types
#pragma once

#include <cstdint>
#include <ostream>

namespace aidin {

enum class GripperStage : uint8_t {
    Reset      = 0,
    Activating = 1,
    Active     = 3,
};

enum class ObjectState : uint8_t {
    Moving        = 0,
    OpenContact   = 1,  // object detected while opening
    ClosedContact = 2,  // object detected while closing
    AtTarget      = 3,
};

struct GripperState {
    bool         activated    = false;  // gACT
    bool         homed        = false;  // gHOM
    bool         goToActive   = false;  // gGTO
    GripperStage stage        = GripperStage::Reset;
    ObjectState  object       = ObjectState::Moving;
    uint8_t      fault        = 0;      // gFLT (0 = OK)
    uint8_t      positionEcho = 0;      // gPR
    uint8_t      position     = 0;      // gPO  0=open, 255=close
    uint8_t      current      = 0;      // gCU
    uint8_t      speed        = 0;      // gSP
    float        voltage      = 0.0f;   // V
    uint8_t      latchedFault = 0;      // gFLTO
};

inline const char* toString(GripperStage s) {
    switch (s) {
        case GripperStage::Reset:      return "Reset";
        case GripperStage::Activating: return "Activating";
        case GripperStage::Active:     return "Active";
    }
    return "Unknown";
}

inline const char* toString(ObjectState o) {
    switch (o) {
        case ObjectState::Moving:        return "Moving";
        case ObjectState::OpenContact:   return "OpenContact";
        case ObjectState::ClosedContact: return "ClosedContact";
        case ObjectState::AtTarget:      return "AtTarget";
    }
    return "Unknown";
}

inline std::ostream& operator<<(std::ostream& os, const GripperState& s) {
    os << "{stage=" << toString(s.stage)
       << " obj="   << toString(s.object)
       << " pos="   << static_cast<int>(s.position)
       << " cur="   << static_cast<int>(s.current)
       << " spd="   << static_cast<int>(s.speed)
       << " V="     << s.voltage
       << " flt="   << static_cast<int>(s.fault)
       << "}";
    return os;
}

} // namespace aidin
