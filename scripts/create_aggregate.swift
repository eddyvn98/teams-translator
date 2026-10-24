import CoreAudio
import Foundation

// Find device UIDs
var propAddress = AudioObjectPropertyAddress(
    mSelector: kAudioHardwarePropertyDevices,
    mScope: kAudioObjectPropertyScopeGlobal,
    mElement: kAudioObjectPropertyElementMain
)

var dataSize: UInt32 = 0
AudioObjectGetPropertyDataSize(AudioObjectID(kAudioObjectSystemObject), &propAddress, 0, nil, &dataSize)
let deviceCount = Int(dataSize) / MemoryLayout<AudioDeviceID>.size
var deviceIDs = [AudioDeviceID](repeating: 0, count: deviceCount)
AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject), &propAddress, 0, nil, &dataSize, &deviceIDs)

var micUID: String? = nil
var blackholeUID: String? = nil

for id in deviceIDs {
    var nameSize = UInt32(MemoryLayout<CFString?>.size)
    var nameProp = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyDeviceNameCFString, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
    var name: CFString?
    AudioObjectGetPropertyData(id, &nameProp, 0, nil, &nameSize, &name)
    
    var uidSize = UInt32(MemoryLayout<CFString?>.size)
    var uidProp = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyDeviceUID, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
    var uid: CFString?
    AudioObjectGetPropertyData(id, &uidProp, 0, nil, &uidSize, &uid)
    
    let strName = (name as String?) ?? ""
    let strUID = (uid as String?) ?? ""
    
    print("Found device: \(strName) (UID: \(strUID))")
    
    if strName == "Teams Hybrid Mic" || strUID == "com.teams_translator.teams_hybrid_mic" {
        print("Aggregate Device 'Teams Hybrid Mic' already exists.")
        exit(0)
    }
    if strName.contains("Micrô") || strName.lowercased().contains("built-in microphone") || (strName.lowercased().contains("macbook") && strUID.contains("Microphone")) {
        micUID = strUID
    }
    if strName.contains("BlackHole") {
        blackholeUID = strUID
    }
}

guard let realMicUID = micUID else {
    print("Error: Could not find real microphone UID")
    exit(1)
}

guard let bhUID = blackholeUID else {
    print("Error: Could not find BlackHole UID")
    exit(1)
}

print("Using Mic: \(realMicUID)")
print("Using BlackHole: \(bhUID)")

let subDevices: [[String: Any]] = [
    [
        kAudioSubDeviceUIDKey as String: realMicUID,
        kAudioSubDeviceDriftCompensationKey as String: 0
    ],
    [
        kAudioSubDeviceUIDKey as String: bhUID,
        kAudioSubDeviceDriftCompensationKey as String: 1
    ]
]

let aggregateUID = "com.teams_translator.teams_hybrid_mic"
let aggregateName = "Teams Hybrid Mic"

let description: [String: Any] = [
    kAudioAggregateDeviceNameKey as String: aggregateName,
    kAudioAggregateDeviceUIDKey as String: aggregateUID,
    kAudioAggregateDeviceSubDeviceListKey as String: subDevices,
    kAudioAggregateDeviceMasterSubDeviceKey as String: realMicUID,
    kAudioAggregateDeviceIsPrivateKey as String: 0,
    kAudioAggregateDeviceIsStackedKey as String: 0
]

var newDeviceID: AudioObjectID = 0
let status = AudioHardwareCreateAggregateDevice(description as CFDictionary, &newDeviceID)

if status == noErr {
    print("Successfully created Aggregate Device '\(aggregateName)' with ID \(newDeviceID)!")
} else {
    print("Failed to create Aggregate Device, status code: \(status)")
    exit(1)
}
