package com.unibe.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.unibe.model.Person;
import com.unibe.repository.EventRepository;

import java.util.List;

@Service
public class FaceRecognitionService {

    private final EventRepository eventRepository;

    @Autowired
    public FaceRecognitionService(EventRepository eventRepository) {
        this.eventRepository = eventRepository;
    }

    public void processFaceRecognition(Person person) {
        // Logic for processing face recognition
        // This could involve saving the detected person to the database
        // and triggering any necessary events or notifications.
    }

    public List<Person> getAllRecognizedPersons() {
        // Logic to retrieve all recognized persons from the database
        return eventRepository.findAll(); // Assuming EventRepository handles Person entities
    }
}