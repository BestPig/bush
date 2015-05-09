<?php
/* Created by BestPig */

class Storage {
	private $_db;
	private $_dataPath;

	public function __construct($sqliteFile, $dataPath) {
		$this->_dataPath = $dataPath;

		$this->_db = new PDO('sqlite:'.$sqliteFile);

		$this->_db->exec("CREATE TABLE IF NOT EXISTS files (
			id INTEGER PRIMARY KEY,
			name TEXT,
			tag TEXT,
			compressed INTEGER)");
	}

	public function getFile($tag) {
		$sql  = "SELECT id, name FROM files WHERE tag = :tag";
		$stmt = $this->_db->prepare($sql);
		$stmt->bindParam(':tag', $tag);
		$stmt->execute();

		$res = $stmt->fetch(PDO::FETCH_ASSOC);

		if ($res) {
			return $res;
		}

		$sql  = "SELECT id, name FROM files WHERE name = :name";
		$stmt = $this->_db->prepare($sql);
		$stmt->bindParam(':name', $tag);
		$stmt->execute();

		$res = $stmt->fetch(PDO::FETCH_ASSOC);

		return $res;
	}

	public function getAllFiles() {
		$sql = "SELECT id, name, tag FROM files";
		$stmt = $this->_db->prepare($sql);
		$stmt->execute();

		$res = $stmt->fetchAll(PDO::FETCH_ASSOC);
		return $res;
	}

	public function deleteFileId($id) {
		$sql = "DELETE FROM files WHERE id = :id";
		$stmt = $this->_db->prepare($sql);
		$stmt->bindParam(':id', $id);
		$stmt->execute();
		@unlink($this->_dataPath.'/'.$id.'.bin');
	}

	public function deleteFileTag($tag) {
		$file = $this->getFile($tag);
		if ($file) {
			$this->deleteFileId($file['id']);
		}
	}

	public function addFile($tag, $name, $compressed) {
		$file = $this->getFile($tag);
		if ($file) {
			$this->deleteFileId($file['id']);
		}
		$sql = "INSERT INTO files (name, tag, compressed) VALUES (:name, :tag, :compressed)";
		$stmt = $this->_db->prepare($sql);
		$stmt->bindParam(':tag', $tag);
		$stmt->bindParam(':name', $name);
		$stmt->bindParam(':compressed', $compressed);
		$stmt->execute();
		return $this->_db->lastInsertId();
	}
}
