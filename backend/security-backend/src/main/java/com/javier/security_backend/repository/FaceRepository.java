package com.javier.security_backend.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.javier.security_backend.model.Face;

@Repository
public interface FaceRepository extends JpaRepository<Face, Long> {
    List<Face> findByFrameId(Long frameId);
    List<Face> findByGender(String gender);
    List<Face> findByEmotion(String emotion);
}
