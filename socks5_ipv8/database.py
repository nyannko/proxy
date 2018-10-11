from pyipv8.ipv8.database import Database

import os

DATABASE_DIRECTORY = os.path.join(u"sqlite")


class ProxyDatabase(Database):
    LATEST_DB_VERSION = 1

    def __init__(self, working_directory, db_name):

        if working_directory != u"memory":
            db_path = os.path.join(working_directory, os.path.join(DATABASE_DIRECTORY, u"%s.db" % db_name))
        else:
            db_path = working_directory

        super(ProxyDatabase, self).__init__(db_path)
        self.db_name = db_name
        self.open()

    def _get(self, query, params):
        return list(self.execute(query, params, fetch_all=False))

    def get_all(self):
        return list(self.execute("SELECT * FROM %s" % self.db_name, (), fetch_all=True))

    def get_last(self):
        return self._get("SELECT * FROM %s ORDER BY timestamp DESC LIMIT 1" % self.db_name, ())

    def get_schema(self):
        return u"""CREATE TABLE IF NOT EXISTS %s (
            timestamp BIGINT NOT NULL, 
            description text, 
            debit real, 
            credit real, 
            balance real)
            """ % self.db_name

    def get_balance(self):
        try:
            balance = self._get(u"SELECT balance FROM %s ORDER BY timestamp DESC LIMIT 1" % self.db_name, ())[0]
        except IndexError as e:
            balance = 0
        return balance

    def debit(self, timestamp, debit, credit, balance):
        self.execute("INSERT INTO %s VALUES (?,'debit', ?, ?, ?)" % self.db_name, (timestamp, debit, credit, balance))
        self.commit()

    def check_database(self, database_version):
        """
        Ensure the proper schema is used by the database.
        :param database_version: Current version of the database.
        :return:
        """
        assert isinstance(database_version, unicode)
        assert database_version.isdigit()
        assert int(database_version) >= 0
        database_version = int(database_version)

        if database_version < self.LATEST_DB_VERSION:
            while database_version < self.LATEST_DB_VERSION:
                upgrade_script = self.get_upgrade_script(current_version=database_version)
                if upgrade_script:
                    self.executescript(upgrade_script)
                database_version += 1
            self.executescript(self.get_schema())
            self.commit()

        return self.LATEST_DB_VERSION

    def get_upgrade_script(self, current_version):
        """
        Return the upgrade script for a specific version.
        :param current_version: the version of the script to return.
        """
        return None
