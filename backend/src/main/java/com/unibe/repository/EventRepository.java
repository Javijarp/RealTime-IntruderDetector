package com.unibe.repository;

import com.unibe.model.DetectionEvent;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface EventRepository extends JpaRepository<DetectionEvent, Long> {
}