import { getLocations } from '@/lib/dal'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'

export const metadata = {
  title: 'Locations — HR-Plus Settings',
}

interface Location {
  id: string
  name: string
  city: string
  country: string
  is_remote: boolean
  is_active: boolean
}

export default async function LocationsPage() {
  let locations: { results: Location[] } = { results: [] }

  try {
    locations = await getLocations()
  } catch {
    // API not available yet
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Locations</h2>
      </div>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>City</TableHead>
              <TableHead>Country</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {locations.results.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
                  No locations found. Connect the API to manage locations.
                </TableCell>
              </TableRow>
            ) : (
              locations.results.map((loc) => (
                <TableRow key={loc.id}>
                  <TableCell className="font-medium">{loc.name}</TableCell>
                  <TableCell>{loc.city}</TableCell>
                  <TableCell>{loc.country}</TableCell>
                  <TableCell>
                    <Badge variant={loc.is_remote ? 'secondary' : 'outline'}>
                      {loc.is_remote ? 'Remote' : 'Office'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={loc.is_active ? 'default' : 'secondary'}>
                      {loc.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
