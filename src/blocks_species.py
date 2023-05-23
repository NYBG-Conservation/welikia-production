# ---------------------------------------------------------------------------
# blocks_species.py
# Creates a shapefile for each input species with probability assigned to each block
# 0.1 kf: basic functionality
# 0.2 kf: using MAXIMUM for zonal stats, not MEAN; add threshold for writing to db
# 0.3 kf: implement writing to mysql
# 0.4 kf: add conditional biodiversity total sum
# ---------------------------------------------------------------------------
# This could really be split into 2-3 tools and linked in ModelBuilder. But not likely to be more widely useful.

# Setup
import sys, string, os, arcgisscripting, MySQLdb
gp = arcgisscripting.create(9.3)
gp.overWriteOutput = 1

# Check out any necessary licenses
gp.CheckOutExtension("spatial")

# Get parameters
# Grids in dirInput should be species only for biodiversity sum -- not other MW elements
dirInput      = gp.GetParameterAsText(0) + os.sep
dirOutput     = gp.GetParameterAsText(1) + os.sep
blocks        = gp.GetParameterAsText(2)

# probThreshold is used to determine:
# 1. whether to add grid to biodiversity sum grid
# 2. whether to write block-species prob record to mysql
# in part to cut down on # of mysql records, and in part as definition of 'likely' species
# We're trying 0 for the moment
# Regardless, probThreshold means application code needs to be aware that NULL value from a LEFT JOIN means '<= probThreshold'
probThreshold = gp.GetParameterAsText(3)

mysqlhost  = gp.GetParameterAsText(4) #'localhost'
mysqluser  = gp.GetParameterAsText(5) #'mannahatta'
mysqlpass  = gp.GetParameterAsText(6) #'W!ldl!fe'
mysqldb    = gp.GetParameterAsText(7) #'themannahattaproject'
mysqltable = gp.GetParameterAsText(8) #'m_blocks_species'
#colltype   = gp.GetParameterAsText(9) #'collection_type'

# Other important vars currently hardcoded: mysql table and column names, zonal aggregation method, grid resolution

# Set directory to specified input parameter and get all rasters in it
gp.workspace = dirInput
MWElements = gp.ListRasters()

# Initialize running biodiversity total grid
Biodiv = None

# Loop over each raster
gp.AddMessage("Starting raster loop...")
for MWElement in MWElements:
   gp.AddMessage("Working on " + MWElement)

   # intermediate data
   zonal1 = dirOutput + 'z' + MWElement
   int2 = dirOutput + 'i' + MWElement
   zonalpolys3 = dirOutput + 'zp' + MWElement + '.shp'

   # Get max of all cells in each block
   gp.ZonalStatistics_sa(blocks, "BID", MWElement, zonal1, "MAXIMUM", "DATA")

   # Turn the result into a rounded integer
   gp.SingleOutputMapAlgebra_sa("int(" + zonal1 + " + .5)", int2)

   # Convert that into polygons -- not simplified, so we have 10m steps
   gp.RasterToPolygon_conversion(int2, zonalpolys3, "NO_SIMPLIFY", "VALUE")

   # Spatial Join: note the -10m search radius ensures we get only the zone polygon actually sitting on top of the block
   gp.SpatialJoin_analysis(blocks, zonalpolys3, dirOutput + MWElement + '_blocks.shp', "JOIN_ONE_TO_ONE", "KEEP_ALL", "BID 'BID' true true false 4 Short 0 4 ,First,#," + blocks + ",BID,-1,-1;prob 'prob' true true false 50 Short 0 0 ,Mean,#," + zonalpolys3 + ",GRIDCODE,-1,-1", "INTERSECTS", "-10 Meters", "")

   # Cleanup
   gp.delete(zonal1)
   gp.delete(int2)
   gp.delete(zonalpolys3)

   # If this is the first MWElement, use it to create the Biodiv grid with all non-null cells = 0
   if Biodiv is None:
      Biodiv = os.path.basename(dirInput.rstrip(os.sep))[0:9] + 'Div'
      gp.SingleOutputMapAlgebra_sa("setnull(IsNull(" + MWElement + "), 0)", dirInput + Biodiv)

   # Add MWElement to running biodiversity total grid
   gp.SingleOutputMapAlgebra_sa(dirInput + Biodiv + " + Con(" + MWElement + " > " + probThreshold + ", 1, 0)", dirInput + Biodiv.rstrip('v') + '1')
   gp.delete(dirInput + Biodiv)
   gp.CopyRaster_management(dirInput + Biodiv.rstrip('v') + '1', dirInput + Biodiv)

gp.delete(dirInput + Biodiv.rstrip('v') + '1')
gp.CheckInExtension("spatial")
gp.AddMessage("Finished outputting block-level species shapefiles.\n")


# Establish db connection
gp.AddMessage("Establishing MySQL db connection...")
try:
   db = MySQLdb.connect(host=mysqlhost, user=mysqluser, passwd=mysqlpass, db=mysqldb)
   # create a cursor
   cursor = db.cursor()

   # Here's where we used to wipe out existing records. But because we're running this on successive taxa, this is a bad idea. Instead, for a fresh run you should just manually empty the db table first.

   # Now loop over every produced shapefile
   gp.workspace = dirOutput
   MWBlocks = gp.ListFeatureClasses()
   gp.AddMessage("Starting shapefile loop...")
   for MWBlock in MWBlocks:
      gp.AddMessage("Working on " + MWBlock)

      # Make sure we have records to operate on
      totalRows = gp.GetCount_management(MWBlock).GetOutput(0)
      #gp.AddMessage('totalRows: ' + totalRows)
      if totalRows <= 0:
         gp.AddMessage(MWBlock + ' has no records.')

      else:
         # extract ElementID from shapefile name
         suffix = MWBlock.rfind('_blocks.shp')
         mwid = MWBlock[1:suffix].replace('_', '.')

         # Start INSERT string
         #MWBlockInsert = "INSERT INTO " + mysqltable + " (bid, mwid, prob, collection_type) VALUES "
         MWBlockInsert = "INSERT INTO " + mysqltable + " (bid, mwid, prob) VALUES "

         # For each shapefile, loop over records and for prob > threshold, add to INSERT string
         MWBlockRows = gp.SearchCursor(MWBlock)
         MWBlockRow = MWBlockRows.next()
         atleastone = False;
         while MWBlockRow:
            if MWBlockRow.prob > int(probThreshold):
               #MWBlockInsert += "(" + str(MWBlockRow.BID) + ", '" + mwid + "', " + str(MWBlockRow.prob) + ", " + colltype + "), "
               MWBlockInsert += "(" + str(MWBlockRow.BID) + ", '" + mwid + "', " + str(MWBlockRow.prob) + "), "
               atleastone = True;
            MWBlockRow = MWBlockRows.next()
         MWBlockInsert = MWBlockInsert.rstrip(', ')

         # write BID, MW ID, and prob for each record in shp to MySQL db
         # prototype: INSERT INTO m_blocks_species VALUES (1, '101.31', 85), (0, '190', 0);
         if atleastone:
            #gp.AddMessage(MWBlockInsert)
            try:
               cursor.execute(MWBlockInsert)
               gp.AddMessage('INSERTed ' + str(cursor.rowcount) + ' records from ' + MWBlock)
            except MySQLdb.Error, e:
               gp.AddMessage("Error %d: %s" % (e.args[0], e.args[1]))
         else:
            gp.AddMessage('No records to INSERT from ' + MWBlock)

   cursor.close()
   db.commit()
   db.close()

   gp.AddMessage("Finished writing block species probabilities to MySQL.\n")

except:
   gp.AddMessage("Could not establish db connection.")
