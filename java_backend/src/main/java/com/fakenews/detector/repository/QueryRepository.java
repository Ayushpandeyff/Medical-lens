
package com.fakenews.detector.repository;

import com.fakenews.detector.entity.Query;
import com.fakenews.detector.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface QueryRepository extends JpaRepository<Query, Long> {
    List<Query> findByUserOrderByCreatedAtDesc(User user);
    List<Query> findTop10ByUserOrderByCreatedAtDesc(User user);
}