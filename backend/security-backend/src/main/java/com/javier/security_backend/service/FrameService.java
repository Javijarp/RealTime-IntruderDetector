package com.javier.security_backend.service;

import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

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
    public Frame saveFrame(byte[] imageData, String imageType, Integer frameNumber) {
        try {
            Frame frame = new Frame();
            frame.setFrameNumber(frameNumber);
            frame.setImageData(imageData);
            frame.setImageType(imageType);
            frame.setTimestamp(Instant.now());

            Frame saved = frameRepository.save(frame);
            log.info("Frame saved successfully - frameId: {} with image size: {} bytes", saved.getId(),
                    imageData.length);
            return saved;
        } catch (Exception e) {
            log.error("Error saving frame", e);
            throw new RuntimeException("Failed to save frame", e);
        }
    }

    public Optional<Frame> getFrameById(Long id) {
        return frameRepository.findById(id);
    }

    public Optional<Frame> getFrameByFrameNumber(Integer frameNumber) {
        return frameRepository.findByFrameNumber(frameNumber);
    }

    public List<Frame> getAllFrames() {
        return frameRepository.findAll();
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

    @Transactional
    public void deleteAllFrames() {
        long count = frameRepository.count();
        frameRepository.deleteAll();
        log.info("Deleted all {} frames from database", count);
    }

    // ═══════════════════════════════════════════════════════════════
    // RECURSIVE FILE SYSTEM OPERATIONS
    // ═══════════════════════════════════════════════════════════════

    /**
     * Recursively delete all files and subdirectories in a directory tree
     * 
     * Use case: Clean up old frame storage directories
     * 
     * Time Complexity: O(n) where n = total files + directories
     * Space Complexity: O(d) where d = maximum depth
     * 
     * @param directory Root directory to delete
     * @return Number of files deleted
     */
    public int deleteFrameDirectoryRecursively(Path directory) {
        log.info("Starting recursive deletion of directory: {}", directory);
        int deletedCount = deleteDirectoryContents(directory);
        log.info("Deleted {} files/directories", deletedCount);
        return deletedCount;
    }

    /**
     * Helper method for recursive directory deletion
     */
    private int deleteDirectoryContents(Path path) {
        int deletedCount = 0;

        if (!Files.exists(path)) {
            return 0; // BASE CASE: path doesn't exist
        }

        try {
            if (Files.isDirectory(path)) {
                // RECURSIVE CASE: process subdirectories first
                try (DirectoryStream<Path> entries = Files.newDirectoryStream(path)) {
                    for (Path entry : entries) {
                        deletedCount += deleteDirectoryContents(entry); // RECURSIVE CALL
                    }
                }
                // Delete the now-empty directory
                Files.delete(path);
                log.debug("Deleted directory: {}", path);
                deletedCount++;
            } else {
                // BASE CASE: delete file
                Files.delete(path);
                deletedCount++;
                log.debug("Deleted file: {}", path);
            }
        } catch (IOException e) {
            log.error("Error deleting: {}", path, e);
        }

        return deletedCount;
    }

    /**
     * Recursively count all files in a directory tree
     * 
     * @param directory Root directory
     * @return Total file count
     */
    public long countFramesRecursively(Path directory) {
        if (!Files.exists(directory)) {
            log.warn("Directory does not exist: {}", directory);
            return 0;
        }

        long count = countFilesInDirectory(directory);
        log.info("Found {} files in {}", count, directory);
        return count;
    }

    /**
     * Helper method for recursive file counting
     */
    private long countFilesInDirectory(Path path) {
        if (!Files.exists(path) || !Files.isDirectory(path)) {
            return 0; // BASE CASE
        }

        long count = 0;
        try (DirectoryStream<Path> entries = Files.newDirectoryStream(path)) {
            for (Path entry : entries) {
                if (Files.isDirectory(entry)) {
                    count += countFilesInDirectory(entry); // RECURSIVE CALL
                } else {
                    count++; // Count this file
                }
            }
        } catch (IOException e) {
            log.error("Error counting files in: {}", path, e);
        }

        return count;
    }

    /**
     * Recursively find all frames matching a pattern
     * 
     * Use case: Find all .jpg files in nested camera folders
     * 
     * @param root    Root directory to search
     * @param pattern Regex pattern to match filenames
     * @return List of matching file paths
     */
    public List<Path> findFramesByPatternRecursively(Path root, String pattern) {
        List<Path> matches = new ArrayList<>();

        if (!Files.exists(root)) {
            log.warn("Root directory does not exist: {}", root);
            return matches;
        }

        searchFiles(root, pattern, matches);
        log.info("Found {} files matching pattern '{}' in {}", matches.size(), pattern, root);
        return matches;
    }

    /**
     * Helper method for recursive file search
     */
    private void searchFiles(Path dir, String pattern, List<Path> accumulator) {
        if (!Files.exists(dir) || !Files.isDirectory(dir)) {
            return; // BASE CASE
        }

        try (DirectoryStream<Path> entries = Files.newDirectoryStream(dir)) {
            for (Path entry : entries) {
                if (Files.isDirectory(entry)) {
                    searchFiles(entry, pattern, accumulator); // RECURSIVE CALL
                } else if (entry.getFileName().toString().matches(pattern)) {
                    accumulator.add(entry);
                }
            }
        } catch (IOException e) {
            log.error("Error searching files in: {}", dir, e);
        }
    }

    /**
     * Calculate total size of all files in a directory tree
     * 
     * @param directory Root directory
     * @return Total size in bytes
     */
    public long calculateDirectorySizeRecursively(Path directory) {
        if (!Files.exists(directory)) {
            log.warn("Directory does not exist: {}", directory);
            return 0;
        }

        long size = calculateSize(directory);
        log.info("Total size of {}: {} bytes ({} MB)",
                directory, size, size / 1024 / 1024);
        return size;
    }

    /**
     * Helper method for recursive size calculation
     */
    private long calculateSize(Path path) {
        if (!Files.exists(path)) {
            return 0; // BASE CASE
        }

        try {
            if (Files.isDirectory(path)) {
                long totalSize = 0;
                try (DirectoryStream<Path> entries = Files.newDirectoryStream(path)) {
                    for (Path entry : entries) {
                        totalSize += calculateSize(entry); // RECURSIVE CALL
                    }
                }
                return totalSize;
            } else {
                return Files.size(path); // BASE CASE: return file size
            }
        } catch (IOException e) {
            log.error("Error calculating size for: {}", path, e);
            return 0;
        }
    }

    /**
     * Get all subdirectories recursively (useful for listing camera folders)
     * 
     * @param root Root directory
     * @return List of all subdirectories
     */
    public List<Path> getAllSubdirectoriesRecursively(Path root) {
        List<Path> subdirs = new ArrayList<>();

        if (!Files.exists(root)) {
            log.warn("Root directory does not exist: {}", root);
            return subdirs;
        }

        collectSubdirectories(root, subdirs);
        log.info("Found {} subdirectories in {}", subdirs.size(), root);
        return subdirs;
    }

    /**
     * Helper method for recursive subdirectory collection
     */
    private void collectSubdirectories(Path dir, List<Path> accumulator) {
        if (!Files.exists(dir) || !Files.isDirectory(dir)) {
            return; // BASE CASE
        }

        try (DirectoryStream<Path> entries = Files.newDirectoryStream(dir)) {
            for (Path entry : entries) {
                if (Files.isDirectory(entry)) {
                    accumulator.add(entry);
                    collectSubdirectories(entry, accumulator); // RECURSIVE CALL
                }
            }
        } catch (IOException e) {
            log.error("Error collecting subdirectories in: {}", dir, e);
        }
    }
}
