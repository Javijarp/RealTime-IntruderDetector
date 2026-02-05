package com.javier.security_backend.service;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.javier.security_backend.dto.FaceDTO;
import com.javier.security_backend.dto.FrameDTO;
import com.javier.security_backend.model.DetectionEvent;
import com.javier.security_backend.model.Face;
import com.javier.security_backend.model.Frame;
import com.javier.security_backend.repository.DetectionEventRepository;
import com.javier.security_backend.repository.FaceRepository;
import com.javier.security_backend.repository.FrameRepository;

@Service
public class FrameService {
    
    private static final Logger log = LoggerFactory.getLogger(FrameService.class);
    
    private final FrameRepository frameRepository;
    private final FaceRepository faceRepository;
    private final DetectionEventRepository detectionEventRepository;
    
    public FrameService(FrameRepository frameRepository, 
                       FaceRepository faceRepository,
                       DetectionEventRepository detectionEventRepository) {
        this.frameRepository = frameRepository;
        this.faceRepository = faceRepository;
        this.detectionEventRepository = detectionEventRepository;
    }
    
    @Transactional
    public Frame saveFrame(FrameDTO dto) {
        log.info("Saving frame {} with {} detected faces", dto.getFrameNumber(), dto.getFaces().size());
        
        try {
            Frame frame = new Frame();
            frame.setFrameNumber(dto.getFrameNumber());
            frame.setImagePath(dto.getImagePath());
            frame.setTimestamp(Instant.parse(dto.getTimestamp()));
            
            // Link to detection event if provided
            if (dto.getDetectionEventId() != null) {
                Optional<DetectionEvent> event = detectionEventRepository.findById(dto.getDetectionEventId());
                event.ifPresent(frame::setDetectionEvent);
            }
            
            // Save frame first
            Frame savedFrame = frameRepository.save(frame);
            
            // Save associated faces
            for (FaceDTO faceDto : dto.getFaces()) {
                Face face = new Face();
                face.setFaceImagePath(faceDto.getFaceImagePath());
                face.setConfidence(faceDto.getConfidence());
                face.setBoundingBox(faceDto.getBoundingBox());
                face.setAge(faceDto.getAge());
                face.setGender(faceDto.getGender());
                face.setEmotion(faceDto.getEmotion());
                face.setFaceEncoding(faceDto.getFaceEncoding());
                face.setFrame(savedFrame);
                
                faceRepository.save(face);
            }
            
            log.info("Frame saved successfully with ID: {}", savedFrame.getId());
            return savedFrame;
        } catch (Exception e) {
            log.error("Error saving frame", e);
            throw e;
        }
    }
    
    public List<Frame> getAllFrames() {
        return frameRepository.findAll();
    }
    
    public Optional<Frame> getFrameById(Long id) {
        return frameRepository.findById(id);
    }
    
    public List<Frame> getFramesByDetectionEvent(Long eventId) {
        return frameRepository.findByDetectionEventId(eventId);
    }
    
    public List<Face> getFacesByFrame(Long frameId) {
        return faceRepository.findByFrameId(frameId);
    }
    
    public List<Face> getFacesByGender(String gender) {
        return faceRepository.findByGender(gender);
    }
    
    public List<Face> getFacesByEmotion(String emotion) {
        return faceRepository.findByEmotion(emotion);
    }
}
