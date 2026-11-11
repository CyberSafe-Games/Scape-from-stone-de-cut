import unittest

import pygame

from src.ui.pose_playback import UNIFORM_TWELVE, PoseBlend, align_stance, display_pose, foot_center, sample_pose


def sprite(x, color=(230, 150, 70)):
    frame = pygame.Surface((72, 72), pygame.SRCALPHA)
    frame.fill(color, (x, 12, 18, 46))
    return frame


class PosePlaybackTests(unittest.TestCase):
    def test_eight_frame_animation_and_twelve_frame_contact_keep_their_exact_pose(self):
        frames = [sprite(12 + index) for index in range(12)]
        self.assertIs(sample_pose(frames[:8], 4, .51, (), True), frames[4])
        self.assertIs(sample_pose(frames, 6, .50, UNIFORM_TWELVE, True, cuts=(6,)), frames[6])

    def test_compatible_twelve_frame_poses_blend_with_an_opaque_shared_body(self):
        frames = [sprite(12 + index, (220 - index * 5, 150, 70)) for index in range(12)]
        pose = sample_pose(frames, 2, 2.36 / 12, UNIFORM_TWELVE, True)
        self.assertIsInstance(pose, PoseBlend)
        rendered, blend_flags = display_pose(pose)
        self.assertEqual(blend_flags, pygame.BLEND_PREMULTIPLIED)
        center = rendered.get_at(rendered.get_bounding_rect().center)
        self.assertEqual(center.a, 255)
        self.assertEqual(rendered.get_at((0, 0)).a, 0)

    def test_transition_keeps_one_solid_outline_when_an_arm_changes_position(self):
        previous = sprite(12)
        previous.fill((230, 150, 70), (30, 19, 8, 6))
        current = sprite(12)
        current.fill((230, 150, 70), (30, 37, 8, 6))
        frames = [previous, previous, current, *([current] * 9)]
        pose = sample_pose(frames, 2, 2.25 / 12, UNIFORM_TWELVE, True)
        self.assertIsInstance(pose, PoseBlend)
        rendered, _ = display_pose(pose)
        self.assertEqual(rendered.get_at((51, 32)).a, 255)
        self.assertEqual(rendered.get_at((51, 58)).a, 0)

    def test_outlier_is_bridged_without_a_second_silhouette(self):
        frames = [sprite(12 + index) for index in range(12)]
        frames[4] = sprite(47)
        pose = sample_pose(frames, 4, 4.5 / 12, UNIFORM_TWELVE, True)
        self.assertIsInstance(pose, PoseBlend)
        self.assertIs(pose.previous, frames[3])
        self.assertIs(pose.current, frames[5])
        rendered, _ = display_pose(pose)
        self.assertLess(rendered.get_bounding_rect().right, 60)
        self.assertIs(sample_pose(frames, 5, 5 / 12, UNIFORM_TWELVE, True), frames[5])

    def test_stance_alignment_preserves_the_ready_foot_center_and_floor(self):
        ready = sprite(8)
        displaced = pygame.Surface(ready.get_size(), pygame.SRCALPHA)
        displaced.blit(ready, (8, -7))
        aligned, = align_stance((displaced,), ready)
        self.assertEqual(foot_center(aligned), foot_center(ready))
        self.assertEqual(aligned.get_bounding_rect().bottom, ready.get_bounding_rect().bottom)
