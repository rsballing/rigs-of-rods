/*
    This source file is part of Rigs of Rods
    Copyright 2005-2012 Pierre-Michel Ricordel
    Copyright 2007-2012 Thomas Fischer
    Copyright 2013-2020 Petr Ohlidal

    For more information, see http://www.rigsofrods.org/

    Rigs of Rods is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License version 3, as
    published by the Free Software Foundation.

    Rigs of Rods is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Rigs of Rods. If not, see <http://www.gnu.org/licenses/>.
*/

#pragma once

#include "Application.h"
#include "RefCountingObject.h"

#include <string>

namespace RoR {

/// @addtogroup Terrain
/// @{

/// Represents an instance of static terrain object (.ODEF file format)
class TerrainEditorObject : public RefCountingObject<TerrainEditorObject>
{
public:
    // Variables are not accessible from AngelScript
    std::string name;
    std::string instance_name;
    std::string type; //!< Accepts "-" as placeholder, otherwise a surveymap icon is registered.
    Ogre::Vector3 position = Ogre::Vector3::ZERO;
    Ogre::Vector3 rotation = Ogre::Vector3::ZERO;
    Ogre::Vector3 initial_position = Ogre::Vector3::ZERO;
    Ogre::Vector3 initial_rotation = Ogre::Vector3::ZERO;
    Ogre::Vector3 initial_scale = Ogre::Vector3::UNIT_SCALE; // ODEF baseline; .tobj does not store per-instance scale.
    int tobj_cache_id = -1;
    std::string tobj_comments;
    // ~ only for static objects:
    Ogre::SceneNode* static_object_node = nullptr;
    std::vector<int> static_collision_boxes;
    std::vector<int> static_collision_tris;
    bool enable_collisions = true;
    EvHandlerFuncID_t script_handler = EVHANDLERFUNCID_INVALID;
    // ~ only for preloaded actors:
    TObjSpecialObject special_object_type = TObjSpecialObject::NONE;
    ActorInstanceID_t actor_instance_id = ACTORINSTANCEID_INVALID;

    // Functions are exported to AngelScript
    Ogre::Vector3 const& getPosition();
    Ogre::Vector3 const& getRotation();
    void setPosition(Ogre::Vector3 const& pos);
    void setRotation(Ogre::Vector3 const& rot);
    std::string const& getName();
    std::string const& getInstanceName();
    std::string const& getType();
    // ~ only for preloaded actors:
    TObjSpecialObject getSpecialObjectType();
    void setSpecialObjectType(TObjSpecialObject type);
    ActorInstanceID_t getActorInstanceId();
    void setActorInstanceId(ActorInstanceID_t instance_id);
};

/// Terrain editing mode; original keyboard controls by Ulteq/2016.
/// * Enter/exit via Ctrl+Y or the ImGui editor/Play controls.
/// * Select scenery from the object list, middle-click, or the original keys.
/// * Move/rotate numerically or with legacy keyboard controls.
/// * Preloaded actors can be selected; their transforms respawn their actor.
/// * Save writes .tobj files for unzipped projects only. Leaving edit mode
///   always writes an editor_out.log fallback (including for zipped maps).
/// * Per-instance size is currently visual-only because .tobj has no scale field.
class TerrainEditor
{
public:
    void UpdateInputEvents(float dt);
    void DrawEditorPanel(); //!< ImGui scene-object browser and transform inspector.
    void WriteSeparateOutputFile(); //!< Writes 'editor_out.log' to 'config' directory - original solution, still used for zipped terrains.
    void WriteEditsToTobjFiles(); //!< Updates existing TOBJ files - new solution, only for projects (unzipped terrains).
    void ClearSelectedObject();
    void SetSelectedObjectByID(TerrainEditorObjectID_t id);
    TerrainEditorObjectID_t GetSelectedObjectID() const;
    const TerrainEditorObjectPtr& FetchSelectedObject();

    static const TerrainEditorObjectPtr TERRAINEDITOROBJECTPTR_NULL; // Dummy value to be returned as const reference.

private:

    bool                m_object_tracking = true;
    char                m_filter[96] = {};
    char                m_new_odef_name[128] = {};
    int                 m_rotation_axis = 1;        //!< 0=X, 1=Y, 2=Z
    std::string         m_last_object_name;

    // Use Get/Set/Clear`SelectedObject()` functions.
    TerrainEditorObjectID_t m_selected_object_id = TERRAINEDITOROBJECTID_INVALID;
};

/// @} // addtogroup Terrain

} // namespace RoR
