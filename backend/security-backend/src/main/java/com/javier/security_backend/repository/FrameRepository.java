package com.javier.security_backend.repository;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.javier.security_backend.model.Frame;

@Repository
public interface FrameRepository extends JpaRepository<Frame, Long> {
    List<Frame> findByDetectionEventId(Long detectionEventId);
    Optional<Frame> findByFrameNumber(Integer frameNumber);
}
